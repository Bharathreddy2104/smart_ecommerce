'use client';

import { useState } from 'react';
import Navbar from '@/components/Navbar';
import { apiFetch } from '@/lib/api';

export default function RegisterPage() {
  const [form, setForm] = useState({ name: '', email: '', password: '' });
  const [message, setMessage] = useState('');

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setMessage('');
    try {
      const data = await apiFetch<{ token: { access: string } }>('/api/auth/register', {
        method: 'POST',
        body: JSON.stringify(form),
      });
      localStorage.setItem('smart_ecom_token', data.token.access);
      const productId = new URLSearchParams(window.location.search).get('add_product');
      if (productId && /^\d+$/.test(productId)) {
        await apiFetch('/api/cart/items', {
          method: 'POST',
          body: JSON.stringify({ product: Number(productId), quantity: 1 }),
        });
        window.location.href = '/cart';
        return;
      }
      window.location.href = '/products';
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Registration failed.');
    }
  };

  return (
    <main className="page-shell">
      <Navbar />
      <form className="form-box" onSubmit={handleSubmit}>
        <h2>Register</h2>
        <input required placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        <input required type="email" autoComplete="email" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <input required minLength={6} type="password" autoComplete="new-password" placeholder="Password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
        <button type="submit">Register</button>
        {message && <p role="alert">{message}</p>}
      </form>
    </main>
  );
}
