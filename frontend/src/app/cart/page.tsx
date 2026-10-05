'use client';

import { useEffect, useState } from 'react';
import Navbar from '@/components/Navbar';
import { apiFetch, formatCurrency } from '@/lib/api';

type CartItem = { id: number; product_id: number; product_name: string; quantity: number; unit_price: number };
type Cart = { items: CartItem[]; subtotal: number; total: number };

export default function CartPage() {
  const [cart, setCart] = useState<Cart>({ items: [], subtotal: 0, total: 0 });
  const [message, setMessage] = useState('Loading cart...');

  async function loadCart() {
    try {
      const data = await apiFetch<Cart>('/api/cart');
      setCart(data);
      setMessage(data.items.length ? '' : 'Your cart is empty.');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Could not load cart.');
    }
  }

  useEffect(() => { void loadCart(); }, []);

  async function setQuantity(item: CartItem, quantity: number) {
    try {
      if (quantity < 1) {
        await apiFetch(`/api/cart/items/${item.id}`, { method: 'DELETE' });
      } else {
        await apiFetch(`/api/cart/items/${item.id}`, { method: 'PUT', body: JSON.stringify({ quantity }) });
      }
      await loadCart();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Could not update cart.');
    }
  }

  return (
    <main className="page-shell">
      <Navbar />
      <h2>Cart</h2>
      <div className="summary-box">
        {cart.items.map((item) => <div className="list-row" key={item.id}>
          <span>{item.product_name} · {formatCurrency(item.unit_price)}</span>
          <span className="quantity-control">
            <button type="button" aria-label={`Remove one ${item.product_name}`} onClick={() => setQuantity(item, item.quantity - 1)}>−</button>
            <span>{item.quantity}</span>
            <button type="button" aria-label={`Add one ${item.product_name}`} onClick={() => setQuantity(item, item.quantity + 1)}>+</button>
            <button type="button" onClick={() => setQuantity(item, 0)}>Remove</button>
          </span>
        </div>)}
        {message && <p role="status">{message}</p>}
        <div className="list-row"><strong>Total</strong><strong>{formatCurrency(cart.total)}</strong></div>
        {cart.items.length > 0 && <a className="primary-btn" href="/checkout">Checkout</a>}
      </div>
    </main>
  );
}
