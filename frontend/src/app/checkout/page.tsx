'use client';

import { useEffect, useState } from 'react';
import Navbar from '@/components/Navbar';
import { apiFetch, formatCurrency } from '@/lib/api';

type Cart = { items: Array<{ id: number; product_name: string; quantity: number; unit_price: number }>; total: number };

export default function CheckoutPage() {
  const [cart, setCart] = useState<Cart>({ items: [], total: 0 });
  const [pendingOrder, setPendingOrder] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('Loading checkout...');

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const sessionId = params.get('session_id');
    const savedOrder = localStorage.getItem('smart_ecom_pending_order');
    if (sessionId && savedOrder) {
      apiFetch(`/api/payments/confirm`, {
        method: 'POST',
        body: JSON.stringify({ order_id: Number(savedOrder), session_id: sessionId }),
      }).then(() => {
        localStorage.removeItem('smart_ecom_pending_order');
        window.location.href = '/orders';
      }).catch((error: unknown) => setMessage(error instanceof Error ? error.message : 'Payment confirmation failed.'));
      return;
    }
    apiFetch<Cart>('/api/cart').then((data) => {
      setCart(data);
      setMessage(data.items.length ? '' : 'Your cart is empty.');
    }).catch((error: unknown) => setMessage(error instanceof Error ? error.message : 'Could not load checkout.'));
  }, []);

  async function placeOrder() {
    setBusy(true);
    setMessage('');
    try {
      const order = await apiFetch<{ id: number }>('/api/orders', { method: 'POST' });
      const payment = await apiFetch<{ checkout_url: string | null; demo: boolean }>('/api/payments/create', {
        method: 'POST',
        body: JSON.stringify({ order_id: order.id }),
      });
      localStorage.setItem('smart_ecom_pending_order', String(order.id));
      if (payment.checkout_url) {
        window.location.assign(payment.checkout_url);
      } else {
        setPendingOrder(order.id);
        setMessage(payment.demo ? 'Stripe test keys are not configured. Use the demo payment button to finish this sample order.' : 'Payment session created.');
      }
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Checkout failed.');
    } finally {
      setBusy(false);
    }
  }

  async function completeDemoPayment() {
    if (!pendingOrder) return;
    setBusy(true);
    try {
      await apiFetch('/api/payments/confirm', { method: 'POST', body: JSON.stringify({ order_id: pendingOrder }) });
      localStorage.removeItem('smart_ecom_pending_order');
      window.location.href = '/orders';
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Demo payment failed.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="page-shell">
      <Navbar />
      <h2>Checkout</h2>
      <div className="summary-box">
        {cart.items.map((item) => <div className="list-row" key={item.id}><span>{item.product_name} × {item.quantity}</span><span>{formatCurrency(Number(item.unit_price) * item.quantity)}</span></div>)}
        <div className="list-row"><strong>Total</strong><strong>{formatCurrency(cart.total)}</strong></div>
        {message && <p role="status">{message}</p>}
        {cart.items.length > 0 && <button type="button" disabled={busy} onClick={placeOrder}>{busy ? 'Processing...' : 'Place order'}</button>}
        {pendingOrder && <button type="button" disabled={busy} onClick={completeDemoPayment}>Complete demo payment</button>}
      </div>
    </main>
  );
}
