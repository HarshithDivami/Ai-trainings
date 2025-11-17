// --- Helper fetches ---
async function fetchState(){ return (await fetch('/state')).json(); }
async function fetchOrders(){ return (await fetch('/orders')).json(); }

// --- Toast system ---
function pushToast(msg, type='info'){ const box=document.getElementById('toasts'); const t=document.createElement('div'); t.className='toast '+type; t.textContent=msg; box.appendChild(t); setTimeout(()=>t.remove(), 4200); }

// --- Render products ---
function renderProducts(inv){ const grid=document.getElementById('products'); grid.innerHTML=''; Object.values(inv).forEach(p=>{ const card=document.createElement('div'); card.className='card'; card.innerHTML=`<img src='${p.image || ''}' alt='${p.name}'/><div class='name'>${p.name}</div><div class='price'>$${p.price.toFixed(2)}</div><div class='stock'>Stock: ${p.stock}</div><button class='quick-add primary small' data-sku='${p.sku}'>Quick Add</button>`; card.addEventListener('click', (e)=>{ if(e.target.classList.contains('quick-add')) return; openProductModal(p); }); grid.appendChild(card); }); }

// --- Transcript ---
function renderTranscript(list){ const root=document.getElementById('transcript'); root.innerHTML=''; list.forEach(turn=>{ const d=document.createElement('div'); d.className='msg '+(turn.role==='agent'?'agent':'user'); d.textContent=(turn.role==='user'?'You: ':'Agent: ')+turn.text; root.appendChild(d); }); root.scrollTop=root.scrollHeight; }

// --- Cart rendering ---
function renderCart(cart){ const lines=document.getElementById('cart-lines'); lines.innerHTML=''; const countEl=document.getElementById('cart-count'); let totalCount=0; Object.values(cart).forEach(line=>{ totalCount+=line.qty; const div=document.createElement('div'); div.className='cart-line'; div.innerHTML=`<div class='meta'><strong>${line.sku}</strong><br/><span>Qty ${line.qty} • $${line.subtotal.toFixed(2)}</span></div><div class='act-btns'><button class='inc small' data-sku='${line.sku}'>+</button><button class='dec small' data-sku='${line.sku}'>-</button><button class='remove danger small' data-sku='${line.sku}'>×</button></div>`; lines.appendChild(div); }); if(!Object.keys(cart).length){ lines.innerHTML='<em class="muted">Empty cart</em>'; } countEl.textContent=totalCount; bindCartButtons(); }

function renderDiscounts(discounts, applied){ const root=document.getElementById('discounts'); root.innerHTML=''; Object.entries(discounts).forEach(([code,pct])=>{ const badge=document.createElement('span'); badge.className='badge'+(applied===code?' active':''); badge.textContent=`${code} ${Math.round(pct*100)}%`; root.appendChild(badge); if(applied!==code){ const b=document.createElement('button'); b.className='small'; b.textContent='Apply'; b.addEventListener('click',()=>applyActions([{type:'apply_discount', code}])); root.appendChild(b);} }); }

function renderOrders(data){ const list=document.getElementById('orders-list'); list.innerHTML=''; if(!data.orders.length){ list.innerHTML='<p class="muted">No orders yet.</p>'; return; } data.orders.slice().reverse().forEach(o=>{ const div=document.createElement('div'); div.className='order'; const lines=o.lines.map(l=>`${l.sku}×${l.qty}`).join(', '); div.innerHTML=`<strong>${o.id}</strong><br/><span>${lines}</span><br/><span>Total: $${o.total_paid.toFixed(2)} ${o.discount_code?`(code ${o.discount_code})`:''}</span>`; div.onclick=()=>openOrderDetail(o); list.appendChild(div); }); }

// --- Actions ---
async function applyActions(actions){ const res=await fetch('/manual',{method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({actions})}); const data=await res.json(); if(data.errors && data.errors.length) data.errors.forEach(e=>pushToast(e,'error')); else pushToast('Updated','success'); await refresh(); }
async function clearCart(){ const r=await fetch('/clear_cart',{method:'POST'}); const d=await r.json(); pushToast('Cart cleared','success'); await refresh(); }
async function removeDiscount(){ const r=await fetch('/remove_discount',{method:'POST'}); await r.json(); pushToast('Discount removed','info'); await refresh(); }
async function sendChat(message){ const res=await fetch('/chat',{method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({message})}); const data=await res.json(); if(data.errors && data.errors.length) data.errors.forEach(e=>pushToast(e,'error')); if(data.actions && data.actions.length) pushToast('Agent applied actions','success'); await refresh(); }
async function checkout(){ const r=await fetch('/checkout',{method:'POST'}); const d=await r.json(); if(d.errors && d.errors.length) d.errors.forEach(e=>pushToast(e,'error')); else pushToast('Checkout complete','success'); await refresh(); }

// --- Product Modal Logic ---
function openProductModal(p){
  const m=document.getElementById('product-modal');
  m.classList.remove('hidden');
  document.getElementById('pm-name').textContent=p.name;
  document.getElementById('pm-img').src=p.image||'';
  document.getElementById('pm-price').textContent='$'+p.price.toFixed(2);
  document.getElementById('pm-stock').textContent='Stock: '+p.stock;
  const thumbs=document.getElementById('pm-thumbs');
  thumbs.innerHTML='';
  (p.gallery||[p.image]).forEach((url,i)=>{
    const t=document.createElement('img');
    t.src=url; t.className='thumb';
    if(i===0) t.classList.add('active');
    t.onclick=()=>{ document.getElementById('pm-img').src=url; thumbs.querySelectorAll('.thumb').forEach(x=>x.classList.remove('active')); t.classList.add('active'); pushToast('Image changed','info'); };
    thumbs.appendChild(t);
  });
  const restockRow=document.getElementById('pm-restock');
  if(p.stock<3){ restockRow.classList.remove('hidden'); } else { restockRow.classList.add('hidden'); }
  document.getElementById('pm-restock-btn').onclick=()=>{ applyActions([{type:'restock', sku:p.sku, qty:5}]); pushToast('Requested restock','success'); };
  document.getElementById('pm-qty').value=1;
  document.getElementById('pm-add').onclick=()=>{ const qty=parseInt(document.getElementById('pm-qty').value)||1; applyActions([{type:'add_to_cart', sku:p.sku, qty}]); closeProductModal(); }; }
function closeProductModal(){ document.getElementById('product-modal').classList.add('hidden'); }

// --- Orders Modal ---
async function openOrders(){ const data=await fetchOrders(); renderOrders(data); document.getElementById('orders-modal').classList.remove('hidden'); }
function closeOrders(){ document.getElementById('orders-modal').classList.add('hidden'); }

// --- Cart Drawer ---
function openCart(){ document.getElementById('cart-drawer').classList.remove('hidden'); }
function closeCart(){ document.getElementById('cart-drawer').classList.add('hidden'); }

// Order detail modal
function openOrderDetail(order){
  const modal=document.getElementById('order-detail-modal');
  modal.classList.remove('hidden');
  document.getElementById('od-id').textContent=order.id;
  const lines=document.getElementById('od-lines'); lines.innerHTML='';
  order.lines.forEach(l=>{ const div=document.createElement('div'); div.className='od-line'; div.textContent=`${l.sku} x${l.qty}`; lines.appendChild(div); });
  document.getElementById('od-total').textContent='Total Paid: $'+order.total_paid.toFixed(2)+(order.discount_code?` (Discount: ${order.discount_code})`:'' );
}
function closeOrderDetail(){ document.getElementById('order-detail-modal').classList.add('hidden'); }

// Bind dynamic cart buttons
function bindCartButtons(){ document.querySelectorAll('.inc').forEach(b=>b.onclick=()=>applyActions([{type:'add_to_cart', sku:b.dataset.sku, qty:1}])); document.querySelectorAll('.dec').forEach(b=>b.onclick=()=>applyActions([{type:'remove_from_cart', sku:b.dataset.sku, qty:1}])); document.querySelectorAll('.remove').forEach(b=>b.onclick=()=>{ fetchState().then(st=>{ const qty=st.cart[b.dataset.sku].qty; applyActions([{type:'remove_from_cart', sku:b.dataset.sku, qty}]); }); }); }

// --- Refresh loop ---
async function refresh(){ const st=await fetchState(); renderProducts(st.inventory); renderCart(st.cart); renderDiscounts(st.discounts, st.applied_discount_code); document.getElementById('total').textContent='$'+st.total.toFixed(2); renderTranscript(st.transcript); // bind quick-add buttons
 document.querySelectorAll('.quick-add').forEach(btn=>btn.onclick=(e)=>{ e.stopPropagation(); applyActions([{type:'add_to_cart', sku:btn.dataset.sku, qty:1}]); }); }

// --- Events ---
document.getElementById('chat-form').addEventListener('submit',e=>{ e.preventDefault(); const inp=document.getElementById('chat-input'); const msg=inp.value.trim(); if(!msg) return; inp.value=''; sendChat(msg); });
document.getElementById('open-cart').addEventListener('click', openCart);
document.getElementById('close-cart').addEventListener('click', closeCart);
document.getElementById('clear-cart').addEventListener('click', clearCart);
document.getElementById('remove-discount').addEventListener('click', removeDiscount);
document.getElementById('checkout').addEventListener('click', checkout);
document.getElementById('open-orders').addEventListener('click', openOrders);
document.getElementById('close-orders').addEventListener('click', closeOrders);
document.getElementById('close-product').addEventListener('click', closeProductModal);
document.getElementById('product-modal').addEventListener('click', (e)=>{ if(e.target.id==='product-modal') closeProductModal(); });
document.getElementById('orders-modal').addEventListener('click', (e)=>{ if(e.target.id==='orders-modal') closeOrders(); });
document.getElementById('close-order-detail').addEventListener('click', closeOrderDetail);
document.getElementById('order-detail-modal').addEventListener('click', e=>{ if(e.target.id==='order-detail-modal') closeOrderDetail(); });

// Initial
refresh();
setInterval(refresh, 9000);
