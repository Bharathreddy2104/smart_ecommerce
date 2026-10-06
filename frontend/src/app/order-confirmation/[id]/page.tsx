'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, useSearchParams } from 'next/navigation';
import Navbar from '@/components/Navbar';
import { apiFetch, formatCurrency } from '@/lib/api';

type Order = {
  id: number;
  total: number | string;
  payment_status: string;
  payment_method: string;
  order_status: string;
  timestamp?: string;
  estimated_delivery?: string | null;
};

const PAYMENT_METHOD_LABELS: Record<string, string> = {
  cash_on_delivery: 'Cash on Delivery',
  online: 'Online Payment',
  debit_card: 'Debit Card',
  credit_card: 'Credit Card',
};

const STATUS_LABELS: Record<string, string> = {
  order_placed: 'Order Placed',
  payment_confirmed: 'Payment Confirmed',
  order_confirmed: 'Order Confirmed',
  processing: 'Processing',
  packed: 'Packed',
  shipped: 'Shipped',
  out_for_delivery: 'Out for Delivery',
  delivered: 'Delivered',
  cancelled: 'Cancelled',
  payment_failed: 'Payment Failed',
  return_requested: 'Return Requested',
  returned: 'Returned',
};

function displayDate(value?: string | null) {
  return value
    ? new Date(value).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })
    : 'To be confirmed';
}

export default function OrderConfirmationPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const orderId = String(params.id);
  const sessionId = searchParams.get('session_id');
  const [order, setOrder] = useState<Order | null>(null);
  const [message, setMessage] = useState('Confirming your order...');

  useEffect(() => {
    let active = true;
    async function loadOrder() {
      try {
        if (sessionId) {
          await apiFetch('/api/payments/confirm', {
            method: 'POST',
            body: JSON.stringify({ order_id: Number(orderId), session_id: sessionId }),
          });
          localStorage.removeItem('smart_ecom_pending_order');
        }
        const data = await apiFetch<Order>(`/api/orders/${orderId}`);
        if (!active) return;
        setOrder(data);
        setMessage('');
      } catch (error) {
        if (active) setMessage(error instanceof Error ? error.message : 'Could not confirm this order.');
      }
    }
    void loadOrder();
    return () => { active = false; };
  }, [orderId, sessionId]);

  const isCod = order?.payment_method === 'cash_on_delivery';

  return (
    <main className="page-shell">
      <Navbar />
      {order ? (
        <section className="confirmation-card">
          <div className="confirmation-check" aria-hidden="true">{order.payment_status === 'paid' || isCod ? '✓' : '!'}</div>
          <p className="eyebrow">{isCod ? 'Pay when it arrives' : order.payment_status === 'paid' ? 'Payment complete' : 'Order received'}</p>
          <h1>Order Placed Successfully!</h1>
          <p className="confirmation-intro">
            {isCod
              ? 'Your order is confirmed. Payment will be collected on delivery.'
              : order.payment_status === 'paid'
                ? 'Thank you. Your payment has been confirmed and we are preparing your order.'
                : `Your order is placed. Payment status: ${order.payment_status}.`}
          </p>
          <div className="confirmation-order-id">Order ID: <strong>#{order.id}</strong></div>
          <div className="confirmation-details">
            <div><span>Payment method</span><strong>{PAYMENT_METHOD_LABELS[order.payment_method] ?? order.payment_method}</strong></div>
            <div><span>Payment status</span><strong className="capitalize">{order.payment_status}</strong></div>
            <div><span>Order status</span><strong>{STATUS_LABELS[order.order_status] ?? order.order_status}</strong></div>
            <div><span>Estimated delivery</span><strong>{displayDate(order.estimated_delivery)}</strong></div>
            <div className="confirmation-total"><span>Order total</span><strong>{formatCurrency(order.total)}</strong></div>
          </div>
          {order.payment_method !== 'cash_on_delivery' && order.payment_status === 'pending' && (
            <p className="payment-security-note">Your payment is not marked paid until the server verifies the Stripe result or demo payment session.</p>
          )}
          <div className="confirmation-actions">
            <Link href={`/orders/${order.id}`} className="primary-btn">Track order</Link>
            <Link href="/products" className="secondary-btn">Continue shopping</Link>
          </div>
        </section>
      ) : (
        <p className="page-status" role="status">{message}</p>
      )}
    </main>
  );
}
