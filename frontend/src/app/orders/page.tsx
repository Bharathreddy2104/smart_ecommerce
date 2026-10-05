'use client';

import { useEffect, useState } from 'react';
import Navbar from '@/components/Navbar';
import { apiFetch, formatCurrency } from '@/lib/api';

type Order = { id: number; total: number; payment_status: string; order_status: string; timestamp?: string };

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [message, setMessage] = useState('Loading orders...');

  useEffect(() => {
    apiFetch<Order[]>('/api/orders').then((items) => {
      setOrders(items);
      setMessage(items.length ? '' : 'No orders yet.');
    }).catch((error: unknown) => setMessage(error instanceof Error ? error.message : 'Could not load orders.'));
  }, []);

  return (
    <main className="page-shell">
      <Navbar />
      <h2>Orders</h2>
      {message && <p role="status">{message}</p>}
      <div className="summary-box">{orders.map((order) => <div className="list-row" key={order.id}>
        <span>Order #{order.id}<small>{order.timestamp ? ` · ${new Date(order.timestamp).toLocaleDateString()}` : ''}</small></span>
        <span>{order.order_status} · {order.payment_status} · {formatCurrency(order.total)}</span>
      </div>)}</div>
    </main>
  );
}
