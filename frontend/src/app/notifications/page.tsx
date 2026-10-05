'use client';

import { useEffect, useState } from 'react';
import Navbar from '@/components/Navbar';
import { API_BASE, apiFetch } from '@/lib/api';

type Notification = { id: number; type: string; message: string; is_read: boolean; timestamp?: string };

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [message, setMessage] = useState('Loading notifications...');

  async function loadNotifications() {
    try {
      const items = await apiFetch<Notification[]>('/api/notifications');
      setNotifications(items);
      setMessage(items.length ? '' : 'No notifications yet.');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Could not load notifications.');
    }
  }

  useEffect(() => {
    void loadNotifications();
    const token = localStorage.getItem('smart_ecom_token');
    if (!token) return;
    const socketUrl = API_BASE.replace(/^http/, 'ws') + `/ws/notifications?token=${encodeURIComponent(token)}`;
    const socket = new WebSocket(socketUrl);
    socket.onmessage = () => { void loadNotifications(); };
    return () => socket.close();
  }, []);

  async function markRead(id: number) {
    try {
      await apiFetch(`/api/notifications/${id}/read`, { method: 'PUT' });
      await loadNotifications();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Could not update notification.');
    }
  }

  return (
    <main className="page-shell">
      <Navbar />
      <h2>Notifications</h2>
      {message && <p role="status">{message}</p>}
      <div className="summary-box">{notifications.map((item) => <div className="list-row" key={item.id}>
        <span>{item.message}<small>{item.timestamp ? ` · ${new Date(item.timestamp).toLocaleString()}` : ''}</small></span>
        {item.is_read ? <span>Read</span> : <button type="button" onClick={() => markRead(item.id)}>Mark read</button>}
      </div>)}</div>
    </main>
  );
}
