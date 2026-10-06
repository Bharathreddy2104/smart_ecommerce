'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import Navbar from '@/components/Navbar';
import { apiFetch } from '@/lib/api';

type Providers = { google: boolean; facebook: boolean; auth0: boolean };

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const [returnProductId, setReturnProductId] = useState('');
  const [returnToRegister, setReturnToRegister] = useState('/register');
  const [providers, setProviders] = useState<Providers>({ google: false, facebook: false, auth0: false });

  useEffect(() => {
    apiFetch<Providers>('/api/auth/providers').then(setProviders).catch(() => undefined);
    const params = new URLSearchParams(window.location.search);
    const productId = params.get('add_product') ?? '';
    if (/^\d+$/.test(productId)) {
      setReturnProductId(productId);
      setReturnToRegister(`/register?${params.toString()}`);
    }
  }, []);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setMessage('');
    try {
      const data = await apiFetch<{ token: { access: string } }>('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      localStorage.setItem('smart_ecom_token', data.token.access);
      const params = new URLSearchParams(window.location.search);
      const productId = params.get('add_product');
      if (productId && /^\d+$/.test(productId)) {
        const requestedQuantity = Number(params.get('quantity'));
        const quantity = Number.isSafeInteger(requestedQuantity) && requestedQuantity > 0 ? requestedQuantity : 1;
        await apiFetch('/api/cart/items', {
          method: 'POST',
          body: JSON.stringify({ product: Number(productId), quantity }),
        });
        window.location.href = params.get('checkout') === '1' ? '/checkout' : '/cart';
        return;
      }
      window.location.href = '/products';
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Login failed.');
    }
  };

  return (
    <main className="page-shell">
      <Navbar />
      <form className="form-box" onSubmit={handleSubmit}>
        <h2>Login</h2>
        <input required type="email" autoComplete="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
        <input required type="password" autoComplete="current-password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
        <button type="submit">Login</button>
        {message && <p role="alert">{message}</p>}
        <p><Link href={returnProductId ? returnToRegister : '/register'}>New customer? Register</Link></p>
        <p className="muted">External sign-in: Google {providers.google ? 'configured' : 'placeholder'}, Facebook {providers.facebook ? 'configured' : 'placeholder'}, Auth0 {providers.auth0 ? 'configured' : 'placeholder'}.</p>
      </form>
    </main>
  );
}
