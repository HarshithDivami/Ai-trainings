"""FastAPI HTML UI for state-aware e-commerce assistant.

Run:
  uvicorn fast_ecommerce_agent:app --reload --port 8000

Features:
- In-memory global state (inventory, cart, discounts)
- Agent interaction endpoint returning JSON actions + message
- Fallback natural language parsing if agent omits action block
- HTML frontend (Jinja2 template) polls state & sends chat messages
"""
from __future__ import annotations
import re
import json
import asyncio
from typing import Dict, Any, List
from dataclasses import dataclass
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from pydantic_ai import Agent

load_dotenv(override=True)
MODEL = "google-gla:gemini-2.5-flash"
agent = Agent(MODEL, system_prompt=(
    "You are an e-commerce assistant managing inventory, cart, discounts, and checkout orders. "
    "For ANY mutation output a fenced JSON block exactly: \n" \
    "```action\n{\"actions\": [{\"type\": \"add_to_cart\", \"sku\": \"SKU1\", \"qty\": 2}]}\n```\n" \
    "Allowed types: add_to_cart, remove_from_cart, apply_discount, restock, checkout. Use given SKUs only (SKU1, SKU2, SKU3). "
    "Never invent SKUs or discount codes. Provide human explanation outside the block; one block max."
))

@dataclass
class Product:
    sku: str
    name: str
    price: float
    stock: int
    image: str
    gallery: list[str]  # new: additional image URLs

INITIAL_INVENTORY: Dict[str, Product] = {
    "SKU1": Product(
        "SKU1","Wireless Mouse",25.99,12,
        "https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=500&q=60",
        [
            "https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=500&q=60",
            "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=500&q=60",
            "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=400&q=50"
        ]
    ),
    "SKU2": Product(
        "SKU2","Mechanical Keyboard",89.50,5,
        "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=500&q=60",
        [
            "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=500&q=60",
            "https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=400&q=55",
            "https://images.unsplash.com/photo-1587202372775-98908bccad4d?auto=format&fit=crop&w=400&q=55"
        ]
    ),
    "SKU3": Product(
        "SKU3","USB-C Hub",42.00,8,
        "https://m.media-amazon.com/images/I/61CJDQiqgqL._SL1500_.jpg",
        [
            "https://images.unsplash.com/photo-1587202372775-98908bccad4d?auto=format&fit=crop&w=500&q=60",
            "https://images.unsplash.com/photo-1603791440384-56cd371ee9a7?auto=format&fit=crop&w=500&q=60",
            "https://images.unsplash.com/photo-1555617117-08fda9a1a5d3?auto=format&fit=crop&w=500&q=60"
        ]
    ),
}
DISCOUNTS = {"SPRING10": 0.10, "VIP25": 0.25}

state: Dict[str, Any] = {
    "inventory": {sku: {**vars(p)} for sku, p in INITIAL_INVENTORY.items()},
    "cart": {},
    "discounts": DISCOUNTS.copy(),
    "applied_discount_code": None,
    "history": [],
    "transcript": [],
    "orders": [],
}

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- Utilities ---

def cart_total() -> float:
    total = sum(item["subtotal"] for item in state["cart"].values())
    code = state["applied_discount_code"]
    if code:
        pct = state["discounts"].get(code, 0)
        total *= (1 - pct)
    return round(total, 2)


def apply_actions(actions: List[Dict[str, Any]]) -> List[str]:
    errors: List[str] = []
    for act in actions:
        t = act.get("type")
        if t == "add_to_cart":
            sku = act.get("sku")
            qty = int(act.get("qty", 1))
            inv = state["inventory"].get(sku)
            if not inv:
                errors.append(f"Unknown SKU {sku}")
                continue
            if qty <= 0:
                errors.append("Quantity must be positive")
                continue
            if inv["stock"] < qty:
                errors.append(f"Insufficient stock for {sku}")
                continue
            inv["stock"] -= qty
            line = state["cart"].setdefault(sku, {"sku": sku, "qty": 0, "subtotal": 0.0})
            line["qty"] += qty
            line["subtotal"] = round(line["qty"] * inv["price"], 2)
        elif t == "remove_from_cart":
            sku = act.get("sku")
            qty = int(act.get("qty", 1))
            line = state["cart"].get(sku)
            inv = state["inventory"].get(sku)
            if not line or not inv:
                errors.append(f"Cannot remove; {sku} not in cart")
                continue
            if qty <= 0:
                errors.append("Quantity must be positive")
                continue
            if line["qty"] < qty:
                errors.append(f"Cart has less than {qty} of {sku}")
                continue
            line["qty"] -= qty
            inv["stock"] += qty
            if line["qty"] == 0:
                del state["cart"][sku]
            else:
                line["subtotal"] = round(line["qty"] * inv["price"], 2)
        elif t == "apply_discount":
            code = act.get("code")
            if code not in state["discounts"]:
                errors.append(f"Unknown discount code {code}")
                continue
            state["applied_discount_code"] = code
        elif t == "restock":
            sku = act.get("sku")
            qty = int(act.get("qty", 0))
            if qty <= 0:
                errors.append("Restock qty must be positive")
                continue
            inv = state["inventory"].get(sku)
            if not inv:
                errors.append(f"Unknown SKU {sku}")
                continue
            inv["stock"] += qty
        elif t == "checkout":
            # create order from current cart
            if not state["cart"]:
                errors.append("Cart is empty; cannot checkout")
                continue
            order = {
                "id": f"ORD{len(state['orders']) + 1:04d}",
                "lines": list(state["cart"].values()),
                "discount_code": state["applied_discount_code"],
                "total_paid": cart_total(),
            }
            state["orders"].append(order)
            # clear cart but keep stock reductions (already deducted when added)
            state["cart"] = {}
            state["applied_discount_code"] = None
        else:
            errors.append(f"Unsupported action type {t}")
    return errors


def parse_action_block(text: str) -> List[Dict[str, Any]]:
    if "```action" not in text:
        return []
    try:
        start = text.index("```action") + len("```action")
        end = text.index("```", start)
        raw = text[start:end].strip("\n")
        data = json.loads(raw)
        return data.get("actions", []) if isinstance(data, dict) else []
    except Exception:
        return []


def guess_actions(text: str) -> List[Dict[str, Any]]:
    tl = text.lower()
    # Name mapping
    name_map = {v["name"].lower(): k for k, v in state["inventory"].items()}
    name_map.update({"mouse": "SKU1", "keyboard": "SKU2", "hub": "SKU3"})

    def find_sku(fragment: str) -> str | None:
        fragment = fragment.strip()
        for n, sku in name_map.items():
            if fragment in n:
                return sku
        return None

    actions: List[Dict[str, Any]] = []
    # Patterns
    add_pat = re.findall(r"\b(?:add|put|insert)\s+(\d+)?\s*([a-zA-Z\- ]+)", tl)
    for qty_str, frag in add_pat:
        sku = find_sku(frag)
        if sku:
            actions.append({"type": "add_to_cart", "sku": sku, "qty": int(qty_str) if qty_str else 1})
    rem_pat = re.findall(r"\b(?:remove|delete|take out)\s+(\d+)?\s*([a-zA-Z\- ]+)", tl)
    for qty_str, frag in rem_pat:
        sku = find_sku(frag)
        if sku:
            actions.append({"type": "remove_from_cart", "sku": sku, "qty": int(qty_str) if qty_str else 1})
    disc_pat = re.findall(r"\b(?:apply|use|activate)\s+code?\s*([A-Z0-9]+)\b", text)
    for code in disc_pat:
        if code in state["discounts"]:
            actions.append({"type": "apply_discount", "code": code})
    rest_pat = re.findall(r"\b(?:restock|replenish|add stock)\s+(\d+)?\s*([a-zA-Z\- ]+)", tl)
    for qty_str, frag in rest_pat:
        sku = find_sku(frag)
        if sku:
            actions.append({"type": "restock", "sku": sku, "qty": int(qty_str) if qty_str else 1})
    return actions


async def run_agent(message: str):
    """Run the agent; support both sync & coroutine return. Always await if needed."""
    try:
        result = agent.run(message, message_history=state["history"])  # may be sync or coroutine
        if asyncio.iscoroutine(result):
            result = await result
        return result
    except Exception:
        return None

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/state")
async def get_state():
    return {
        "inventory": state["inventory"],
        "cart": state["cart"],
        "discounts": state["discounts"],
        "applied_discount_code": state["applied_discount_code"],
        "total": cart_total(),
        "transcript": state["transcript"],
    }

@app.post("/chat")
async def chat(req: Dict[str, Any]):
    user_msg = req.get("message", "").strip()
    if not user_msg:
        return JSONResponse({"error": "empty message"}, status_code=400)
    state["transcript"].append({"role": "user", "text": user_msg})
    result = await run_agent(user_msg)
    output = result.output if (result and hasattr(result, "output")) else (str(result) if result else "(agent failed)")
    actions = parse_action_block(output)
    if not actions:
        # Try agent output then user message
        actions = guess_actions(output) or guess_actions(user_msg)
    if actions:
        errs = apply_actions(actions)
    else:
        errs = []
    state["transcript"].append({"role": "agent", "text": output})
    if result and hasattr(result, "all_messages"):
        state["history"] = result.all_messages()
    return {
        "agent": output,
        "actions": actions,
        "errors": errs,
        "cart": state["cart"],
        "inventory": state["inventory"],
        "total": cart_total(),
    }

@app.post("/manual")
async def manual(req: Dict[str, Any]):
    actions = req.get("actions", [])
    if not isinstance(actions, list):
        return JSONResponse({"error": "actions must be list"}, status_code=400)
    errs = apply_actions(actions)
    return {"errors": errs, "cart": state["cart"], "inventory": state["inventory"], "total": cart_total()}

@app.post("/clear_cart")
async def clear_cart():
    # remove all items (return stock)
    actions = [{"type": "remove_from_cart", "sku": sku, "qty": line["qty"]} for sku, line in list(state["cart"].items())]
    apply_actions(actions)
    return {"cart": state["cart"], "inventory": state["inventory"], "total": cart_total()}

@app.post("/remove_discount")
async def remove_discount():
    state["applied_discount_code"] = None
    return {"applied_discount_code": None, "total": cart_total()}

@app.get("/orders")
async def get_orders():
    return {"orders": state["orders"]}

@app.post("/checkout")
async def checkout():
    errs = apply_actions([{"type": "checkout"}])
    return {"errors": errs, "orders": state["orders"], "total": cart_total()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("fast_ecommerce_agent:app", host="127.0.0.1", port=8001, reload=True)
