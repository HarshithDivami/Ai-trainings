# Async Console Chatbot

Simple async console chatbot using `pydantic_ai` with retry logic, persistent history, and Logfire instrumentation.

## Features
- Model selection via `MODEL` env var (default: `google-gla:gemini-2.5-flash`)
- Optional system prompt via `SYSTEM_PROMPT`
- Persistent conversation history to JSON (`HISTORY_FILE`)
- Graceful exit on `exit`, `quit`, or `bye`
- Basic exponential backoff retries (`MAX_RETRIES`, `BACKOFF_FACTOR`)
- Logfire instrumentation (falls back to local-only if not authenticated)
- Gemini key alias support: `GEMINI_API_KEY` maps automatically to `GOOGLE_API_KEY`

## Environment Variables
| Name | Purpose | Default |
|------|---------|---------|
| MODEL | Provider + model id (e.g. `google-gla:gemini-2.5-flash`) | google-gla:gemini-2.5-flash |
| SYSTEM_PROMPT | System instructions for assistant | "You are a helpful assistant." |
| HISTORY_FILE | JSON file for storing chat history (set empty to disable) | .chat_history.json |
| MAX_RETRIES | API retry attempts | 3 |
| BACKOFF_FACTOR | Base seconds for exponential backoff | 1.5 |
| GOOGLE_API_KEY | Google Gemini API key (can use `GEMINI_API_KEY` instead) | — |
| GEMINI_API_KEY | Alias for `GOOGLE_API_KEY` | — |
| OPENAI_API_KEY | OpenAI API key (used if MODEL starts with `openai`) | — |
| FALLBACK_MODEL | Optional fallback model if primary provider key missing | — |

## Gemini Setup
Add your Gemini key to a `.env` file as either:
```
GEMINI_API_KEY=your_gemini_key_here
```
Or:
```
GOOGLE_API_KEY=your_gemini_key_here
```
If you only set `GEMINI_API_KEY`, the app will alias it to `GOOGLE_API_KEY` automatically.

## Running
1. Create and populate `.env`.
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Start chatbot:
```bash
python chatbot.py
```
4. Type messages; use `exit`, `quit`, or `bye` to end.

## E-commerce UI Agent (State-Aware)
A Streamlit app (`ui_ecommerce_agent.py`) showcases multi-turn UI state manipulation.

### Start UI
```bash
streamlit run ui_ecommerce_agent.py
```

### Fast HTML UI (FastAPI)
For a faster, lightweight HTML interface use `fast_ecommerce_agent.py`:
```bash
uvicorn fast_ecommerce_agent:app --reload --port 8000
```
Open http://localhost:8000 in your browser.

Legacy Features (original UI):
- Responsive HTML/JS front-end (inventory, cart, discounts, chat)
- Real-time cart updates via REST endpoints
- Agent + natural language fallback parsing
- Manual controls for add/remove/apply/clear actions

Modern Refresh (2025):
- Product cards with images & hover elevation
- Slide-in cart drawer with quantity controls
- Order history modal & checkout workflow
- Product quick-view modal for manual quantity add
- Toast notifications (success/error/info) for all mutations
- Dark glass topbar + responsive grid layout
- Expanded actions: adds checkout & persistent orders

Updated Endpoints:
- GET `/state` current state snapshot
- POST `/chat` {"message": "add 2 mouse"}
- POST `/manual` {"actions": [{"type":"add_to_cart","sku":"SKU1","qty":2}]}
- POST `/clear_cart`
- POST `/remove_discount`
- POST `/checkout` finalize current cart into order
- GET `/orders` list prior orders

To customize styling edit `static/style.css`.


### Capabilities
- Dual interaction: manual UI controls + AI assistant actions
- Inventory panel with per-product quantity selector & Add buttons
- Cart panel with + / - / Remove controls & Clear Cart
- Discount panel with Apply code buttons & Remove discount
- Agent can emit fenced JSON action blocks to mutate state
- Supported actions: `add_to_cart`, `remove_from_cart`, `apply_discount`, `restock`, `checkout`
- Right panel continuously introspects current state
- Theming: dark gradient background, visually distinct user vs agent message blocks

### Sample 3+ Turn Conversation
Turn 1 (You): List products and add 2 Wireless Mouse to my cart.
Turn 1 (Agent): Adds SKU1 (2 units) via action block; cart shows 2, inventory stock drops.
Turn 2 (You): Apply SPRING10 discount and restock the mouse by 3.
Turn 2 (Agent): Discount applied, inventory SKU1 +3, total reflects 10% off.
Turn 3 (You): Remove 1 mouse from cart and summarize current total.
Turn 3 (Agent): Cart qty decreases to 1, subtotal updates, total recalculated.
Turn 4 (Optional You): Add 1 USB-C Hub and show final summary.
Turn 4 (Agent): Adds SKU3; final total with discount displayed.

### Action Block Format
Agent may append fenced block:
```
```action
{"actions": [{"type": "add_to_cart", "sku": "SKU1", "qty": 2}]}
```
```
Multiple actions allowed in one block. Invalid actions surface warnings.

### Manual Control Examples
1. Use inventory Add button to insert items without the agent.
2. Adjust quantities directly in Cart panel (+ / -) to see stock update in Inventory.
3. Apply discount via button; remove discount with Remove Discount.
4. Clear Cart returns all stock to inventory.

### Styling
Custom CSS (see `static/style.css`) now includes dark theme, product grid, modals, drawer, toast notifications, and responsive behaviors.

Quick customization:
- Change accent color: edit `--accent` & `--accent-grad` in `:root`.
- Adjust toast lifetime: change `setTimeout` duration in `pushToast` (in `static/app.js`).
- Add new SKU image: extend `INITIAL_INVENTORY` in `fast_ecommerce_agent.py` with `image` URL.

### Demo Goals Alignment
- Build e-commerce assistant: Implemented product inventory & cart logic.
- Demonstrate UI state manipulation: Actions mutate Streamlit session state.
- Show state introspection: Side panel with inventory, cart, discounts, total.
- 3+ turns conversation included above.

## Files
- `chatbot.py`: Minimal basic chatbot.
- `chatbot_basic.py`: Also minimal; similar to `chatbot.py` (keep one if desired).
- `chatbot_advanced.py`: Advanced features (history, retries, fallbacks).

## Basic Version
A minimal version is provided in `chatbot_basic.py`:
```bash
python chatbot_basic.py
```
Set `GOOGLE_API_KEY` (or `GEMINI_API_KEY`) in `.env` for Gemini models, or `OPENAI_API_KEY` for OpenAI models.

## History Persistence
Set `HISTORY_FILE` in `.env` to control where history is stored. Example:
```
HISTORY_FILE=.chat_history.json
```
Disable persistence by setting it to an empty value:
```
HISTORY_FILE=
```

## Fallback Logic
- If `MODEL` starts with `google` but no Gemini key is found, the bot tries fallback to an OpenAI model if an `OPENAI_API_KEY` is present.
- If `MODEL` starts with `openai` but you only have a Gemini key, it switches to the default Gemini model.

## Error Handling & Retries
On transient errors, the bot retries with exponential backoff: `sleep = BACKOFF_FACTOR * 2^(attempt-1)`.

## Notes
- Update dependencies if you hit import errors:
```bash
pip install -U logfire pydantic-ai pydantic-graph
```
- Logfire instrumentation is best-effort; warnings will not stop the chatbot.

## License
MIT (adjust as needed).
