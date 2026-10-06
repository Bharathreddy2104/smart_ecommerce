'use client';

import { useEffect, useRef, useState } from 'react';
import Navbar from '@/components/Navbar';
import { apiFetch, formatCurrency } from '@/lib/api';

type Cart = { items: Array<{ id: number; product_name: string; quantity: number; unit_price: number }>; total: number };
type PaymentMethod = 'cash_on_delivery' | 'online' | 'debit_card' | 'credit_card';

const PAYMENT_METHODS: Array<{ value: PaymentMethod; label: string; detail: string; icon: string }> = [
  { value: 'cash_on_delivery', label: 'Cash on Delivery', detail: 'Pay when your order arrives.', icon: '🚚' },
  { value: 'online', label: 'Online Payment', detail: 'Secure online payment with Stripe or demo checkout.', icon: '🔒' },
  { value: 'debit_card', label: 'Debit Card', detail: 'Pay securely using a debit card.', icon: '💳' },
  { value: 'credit_card', label: 'Credit Card', detail: 'Pay securely using a credit card.', icon: '💳' },
];

export default function CheckoutPage() {
  const [cart, setCart] = useState<Cart>({ items: [], total: 0 });
  const [shippingAddress, setShippingAddress] = useState('');
  const [addressError, setAddressError] = useState('');
  const addressInput = useRef<HTMLTextAreaElement>(null);
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('online');
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
        window.location.href = `/order-confirmation/${savedOrder}`;
      }).catch((error: unknown) => setMessage(error instanceof Error ? error.message : 'Payment confirmation failed.'));
      return;
    }
    if (params.get('cancelled') === '1') {
      setMessage('Payment was not completed. Your order is saved as pending; you can review it from your orders.');
    }
    apiFetch<Cart>('/api/cart').then((data) => {
      setCart(data);
      if (data.items.length && params.get('cancelled') !== '1') setMessage('');
      else if (!data.items.length && params.get('cancelled') !== '1') setMessage('Your cart is empty.');
    }).catch((error: unknown) => setMessage(error instanceof Error ? error.message : 'Could not load checkout.'));
  }, []);

  async function placeOrder() {
    if (!shippingAddress.trim()) {
      setAddressError('Enter your delivery address to place this order.');
      addressInput.current?.focus();
      return;
    }
    setAddressError('');
    setBusy(true);
    setMessage('');
    try {
      const order = await apiFetch<{ id: number }>('/api/orders', {
        method: 'POST',
        body: JSON.stringify({
          shipping_address: shippingAddress.trim(),
          payment_method: paymentMethod,
        }),
      });
      if (paymentMethod === 'cash_on_delivery') {
        window.location.href = `/order-confirmation/${order.id}`;
        return;
      }
      const payment = await apiFetch<{ checkout_url: string | null; demo: boolean }>('/api/payments/create', {
        method: 'POST',
        body: JSON.stringify({ order_id: order.id }),
      });
      localStorage.setItem('smart_ecom_pending_order', String(order.id));
      if (payment.checkout_url) {
        window.location.assign(payment.checkout_url);
      } else {
        setPendingOrder(order.id);
        setMessage(payment.demo
          ? 'DEMO PAYMENT: Stripe test credentials are not configured. Complete this simulated payment to confirm the order.'
          : 'Secure payment session created.');
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
      window.location.href = `/order-confirmation/${pendingOrder}`;
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
        {cart.items.length > 0 && (
          <label className="address-field">
            Delivery address
            <textarea
              required
              ref={addressInput}
              aria-invalid={Boolean(addressError)}
              aria-describedby={addressError ? 'delivery-address-error' : 'delivery-address-help'}
              autoComplete="street-address"
              rows={3}
              value={shippingAddress}
              onChange={(event) => {
                setShippingAddress(event.target.value);
                if (event.target.value.trim()) setAddressError('');
              }}
              placeholder="Enter your delivery address"
            />
            {addressError
              ? <span className="address-error" id="delivery-address-error" role="alert">{addressError}</span>
              : <span className="address-help" id="delivery-address-help">Required so we can prepare shipment and delivery tracking.</span>}
          </label>
        )}
        {cart.items.length > 0 && (
          <fieldset className="payment-method-fieldset">
            <legend>Payment Method</legend>
            <div className="payment-method-options">
              {PAYMENT_METHODS.map((method) => (
                <label className={`payment-method-option${paymentMethod === method.value ? ' is-selected' : ''}`} key={method.value}>
                  <input
                    type="radio"
                    name="payment_method"
                    value={method.value}
                    checked={paymentMethod === method.value}
                    onChange={() => setPaymentMethod(method.value)}
                  />
                  <span className="payment-method-icon" aria-hidden="true">{method.icon}</span>
                  <span className="payment-method-copy">
                    <strong>{method.label}</strong>
                    <small>{method.detail}</small>
                  </span>
                  <span className="payment-radio-indicator" aria-hidden="true" />
                </label>
              ))}
            </div>
            {paymentMethod !== 'cash_on_delivery' && (
              <p className="payment-security-note">Card details are entered only on Stripe Checkout. SmartCart never stores card numbers, CVV or PIN.</p>
            )}
          </fieldset>
        )}
        {message && <p role="status">{message}</p>}
        {cart.items.length > 0 && (
          <button type="button" disabled={busy} onClick={placeOrder}>
            {busy ? 'Processing...' : paymentMethod === 'cash_on_delivery' ? 'Place COD order' : 'Continue to secure payment'}
          </button>
        )}
        {pendingOrder && (
          <button type="button" className="demo-payment-button" disabled={busy} onClick={completeDemoPayment}>
            {busy ? 'Confirming...' : 'Complete demo payment'}
          </button>
        )}
      </div>
    </main>
  );
}
