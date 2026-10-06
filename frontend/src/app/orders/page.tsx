'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import Navbar from '@/components/Navbar';
import { apiFetch, formatCurrency } from '@/lib/api';

type OrderItem = {
  id: number;
  product_id: number;
  product_name: string;
  quantity: number;
  price: number | string;
};

type Order = {
  id: number;
  total: number | string;
  payment_status: string;
  payment_method: string;
  order_status: string;
  timestamp?: string;
  estimated_delivery?: string | null;
  tracking_number?: string;
  items: OrderItem[];
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

const PAYMENT_METHOD_LABELS: Record<string, string> = {
  cash_on_delivery: 'Cash on Delivery',
  online: 'Online Payment',
  debit_card: 'Debit Card',
  credit_card: 'Credit Card',
};

function displayDate(value?: string | null) {
  if (!value) return 'Not available';
  return new Date(value).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
}

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [message, setMessage] = useState('Loading orders...');

  useEffect(() => {
    apiFetch<Order[]>('/api/orders').then((items) => {
      setOrders(items);
      setMessage(items.length ? '' : 'No orders yet. Your next favorite is waiting.');
    }).catch((error: unknown) => setMessage(error instanceof Error ? error.message : 'Could not load orders.'));
  }, []);

  return (
    <main className="page-shell">
      <Navbar />
      <section className="catalog-heading">
        <div>
          <p className="eyebrow">Your SmartCart purchases</p>
          <h1>Your orders</h1>
          <p>Follow each order from checkout to your doorstep.</p>
        </div>
        <Link href="/products" className="secondary-btn">Continue shopping</Link>
      </section>
      {message && <p className="page-status" role="status">{message}</p>}
      <div className="orders-list">
        {orders.map((order) => (
          <article className="order-card" key={order.id}>
            <div className="order-card-header">
              <div>
                <span className="order-overline">Order #{order.id}</span>
                <p>Placed {displayDate(order.timestamp)}</p>
              </div>
              <span className={`order-status-pill status-${order.order_status}`}>
                {STATUS_LABELS[order.order_status] ?? order.order_status}
              </span>
            </div>
            <div className="order-items">
              {order.items.map((item) => (
                <div className="order-item-row" key={item.id}>
                  <Link href={`/products/${item.product_id}`}>{item.product_name}</Link>
                  <span>Qty {item.quantity}</span>
                  <span>{formatCurrency(Number(item.price) * item.quantity)}</span>
                </div>
              ))}
            </div>
            <div className="order-summary-grid">
              <div><span>Total</span><strong>{formatCurrency(order.total)}</strong></div>
              <div><span>Payment</span><strong>{PAYMENT_METHOD_LABELS[order.payment_method] ?? order.payment_method}<small className="capitalize">{order.payment_status}</small></strong></div>
              <div><span>Estimated delivery</span><strong>{displayDate(order.estimated_delivery)}</strong></div>
              <div><span>Tracking number</span><strong>{order.tracking_number || 'Assigned when shipped'}</strong></div>
            </div>
            <div className="order-card-footer">
              <Link href={`/orders/${order.id}`} className="primary-btn">Track order</Link>
              <span className="muted">{order.items.length} {order.items.length === 1 ? 'product' : 'products'}</span>
            </div>
          </article>
        ))}
      </div>
    </main>
  );
}
