'use client';

import { useEffect, useState } from 'react';
import Navbar from '@/components/Navbar';
import { apiFetch } from '@/lib/api';

type User = { name: string; email: string; role: string };

export default function ProfilePage() {
  const [user, setUser] = useState<User | null>(null);
  const [message, setMessage] = useState('Loading profile...');

  useEffect(() => {
    apiFetch<User>('/api/auth/me').then((profile) => {
      setUser(profile);
      setMessage('');
    }).catch((error: unknown) => setMessage(error instanceof Error ? error.message : 'Could not load profile.'));
  }, []);

  return (
    <main className="page-shell">
      <Navbar />
      <h2>Profile</h2>
      {user ? <div className="summary-box"><p>Name: {user.name}</p><p>Email: {user.email}</p><p>Role: {user.role}</p></div> : <p role="status">{message}</p>}
    </main>
  );
}
