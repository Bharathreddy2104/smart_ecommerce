'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useParams } from 'next/navigation';
import Navbar from '@/components/Navbar';
import { apiFetch, formatCurrency, mediaUrl } from '@/lib/api';

type OrderItem = {
  id: number;
  product_id: number;
  product_name: string;
  product_image?: string | null;
  quantity: number;
  price: number | string;
};

type StatusEvent = { id: number; status: string; timestamp?: string | null };

type Order = {
  id: number;
  customer_name?: string;
  customer_email?: string;
  total: number | string;
  payment_status: string;
  payment_method: string;
  order_status: string;
  timestamp?: string;
  shipping_address?: string;
  tracking_number?: string;
  carrier_name?: string;
  shipped_at?: string | null;
  estimated_delivery?: string | null;
  items: OrderItem[];
  status_history: StatusEvent[];
};

const DELIVERY_STEPS = [
  { status: 'order_placed', label: 'Order Placed', detail: 'We received your order.' },
  { status: 'payment_confirmed', label: 'Payment Confirmed', detail: 'Your payment was confirmed.' },
  { status: 'order_confirmed', label: 'Order Confirmed', detail: 'Your order is confirmed.' },
  { status: 'processing', label: 'Processing', detail: 'We are preparing your items.' },
  { status: 'packed', label: 'Packed', detail: 'Your items are packed and ready.' },
  { status: 'shipped', label: 'Shipped', detail: 'Your order is on the way.' },
  { status: 'out_for_delivery', label: 'Out for Delivery', detail: 'Your order is on its final delivery route.' },
  { status: 'delivered', label: 'Delivered', detail: 'Your order has arrived.' },
];

const STATUS_LABELS: Record<string, string> = {
  ...Object.fromEntries(DELIVERY_STEPS.map((step) => [step.status, step.label])),
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

function displayDate(value?: string | null, includeTime = false) {
  if (!value) return '';
  const options: Intl.DateTimeFormatOptions = includeTime
    ? { day: 'numeric', month: 'short', year: 'numeric', hour: 'numeric', minute: '2-digit' }
    : { day: 'numeric', month: 'long', year: 'numeric' };
  return new Date(value).toLocaleString('en-IN', options);
}

export default function OrderDetailPage() {
  const params = useParams();
  const id = String(params.id);
  const [order, setOrder] = useState<Order | null>(null);
  const [message, setMessage] = useState('Loading order details...');

  useEffect(() => {
    apiFetch<Order>(`/api/orders/${id}`).then((data) => {
      setOrder(data);
      setMessage('');
    }).catch((error: unknown) => setMessage(error instanceof Error ? error.message : 'Could not load this order.'));
  }, [id]);

  if (!order) {
    return (
      <main className="page-shell">
        <Navbar />
        <p className="page-status" role="status">{message}</p>
        <Link href="/orders" className="secondary-btn">Back to orders</Link>
      </main>
    );
  }

  const eventByStatus = new Map(order.status_history.map((event) => [event.status, event]));
  const currentStepIndex = DELIVERY_STEPS.findIndex((step) => step.status === order.order_status);
  const latestCompletedStep = DELIVERY_STEPS.reduce(
    (last, step, index) => eventByStatus.has(step.status) ? index : last,
    currentStepIndex,
  );
  const nonDeliveryStatus = !DELIVERY_STEPS.some((step) => step.status === order.order_status);

  return (
    <main className="page-shell">
      <Navbar />
      <div className="tracking-back"><Link href="/orders">← Back to your orders</Link></div>
      <section className="tracking-heading">
        <div>
          <p className="eyebrow">Order tracking</p>
          <h1>Order #{order.id}</h1>
          <p>Placed {displayDate(order.timestamp)}</p>
        </div>
        <span className={`order-status-pill status-${order.order_status}`}>
          {STATUS_LABELS[order.order_status] ?? order.order_status}
        </span>
      </section>

      {nonDeliveryStatus && (
        <div className={`tracking-alert status-${order.order_status}`} role="status">
          Current order status: <strong>{STATUS_LABELS[order.order_status] ?? order.order_status}</strong>
        </div>
      )}

      <div className="tracking-layout">
        <div className="tracking-main">
          <section className="tracking-panel">
            <div className="panel-heading">
              <div><p className="eyebrow">Live order progress</p><h2>Delivery timeline</h2></div>
              <span className="current-stage">{STATUS_LABELS[order.order_status] ?? order.order_status}</span>
            </div>
            <ol className="delivery-timeline">
              {DELIVERY_STEPS.map((step, index) => {
                const event = eventByStatus.get(step.status);
                const complete = Boolean(event) || index < latestCompletedStep;
                const active = step.status === order.order_status;
                return (
                  <li
                    className={`timeline-step${complete ? ' is-complete' : ''}${active ? ' is-current' : ''}`}
                    key={step.status}
                  >
                    <span className="timeline-marker" aria-hidden="true">{active ? '●' : complete ? '✓' : ''}</span>
                    <div className="timeline-copy">
                      <div className="timeline-label-row">
                        <strong>{step.label}</strong>
                        {active && <span className="timeline-now">Current</span>}
                      </div>
                      <p>{step.detail}</p>
                      {event?.timestamp && <time dateTime={event.timestamp}>{displayDate(event.timestamp, true)}</time>}
                    </div>
                  </li>
                );
              })}
            </ol>
          </section>

          <section className="tracking-panel">
            <div className="panel-heading">
              <div><p className="eyebrow">In this order</p><h2>Products</h2></div>
              <strong>{formatCurrency(order.total)}</strong>
            </div>
            <div className="tracking-items">
              {order.items.map((item) => {
                const image = mediaUrl(item.product_image);
                return (
                  <div className="tracking-item" key={item.id}>
                    <span className="tracking-item-image">
                      {image
                        ? <Image src={image} alt="" fill sizes="58px" unoptimized />
                        : <span className="tracking-item-placeholder" aria-hidden="true">□</span>}
                    </span>
                    <div className="tracking-item-name">
                      <Link href={`/products/${item.product_id}`}>{item.product_name}</Link>
                      <span>Quantity: {item.quantity}</span>
                    </div>
                    <strong>{formatCurrency(Number(item.price) * item.quantity)}</strong>
                  </div>
                );
              })}
            </div>
          </section>
        </div>

        <aside className="tracking-sidebar">
          <section className="tracking-panel shipment-panel">
            <p className="eyebrow">Shipment</p>
            <h2>Delivery details</h2>
            <dl className="shipment-details">
              <div><dt>Carrier</dt><dd>{order.carrier_name || 'SmartCart Express'}</dd></div>
              <div><dt>Tracking number</dt><dd>{order.tracking_number || 'Assigned when shipped'}</dd></div>
              <div><dt>Estimated delivery</dt><dd>{displayDate(order.estimated_delivery) || 'To be confirmed'}</dd></div>
              {order.shipped_at && <div><dt>Shipping date</dt><dd>{displayDate(order.shipped_at)}</dd></div>}
              <div><dt>Delivery address</dt><dd>{order.shipping_address || 'No address was saved for this order.'}</dd></div>
            </dl>
          </section>

          <section className="tracking-panel payment-panel">
            <p className="eyebrow">Payment</p>
            <h2>Order summary</h2>
            <div className="payment-summary-row"><span>Payment method</span><strong>{PAYMENT_METHOD_LABELS[order.payment_method] ?? order.payment_method}</strong></div>
            <div className="payment-summary-row"><span>Payment status</span><strong className="capitalize">{order.payment_status}</strong></div>
            <div className="payment-summary-row"><span>Products ({order.items.reduce((count, item) => count + item.quantity, 0)})</span><strong>{formatCurrency(order.total)}</strong></div>
            <div className="payment-summary-row payment-total"><span>Total paid</span><strong>{formatCurrency(order.total)}</strong></div>
          </section>
        </aside>
      </div>
    </main>
  );
}
