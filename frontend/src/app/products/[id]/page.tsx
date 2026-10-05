'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Navbar from '@/components/Navbar';
import { ApiRequestError, apiFetch, formatCurrency, mediaUrl } from '@/lib/api';

type Product = { id: number; name: string; description: string; price: number; stock: number; image?: string | null };

export default function ProductDetailPage() {
  const params = useParams();
  const id = String(params.id);
  const [product, setProduct] = useState<Product | null>(null);
  const [message, setMessage] = useState('Loading product...');

  useEffect(() => {
    apiFetch<Product>(`/api/products/${id}`).then((item) => {
      setProduct(item);
      setMessage('');
    }).catch((error: unknown) => setMessage(error instanceof Error ? error.message : 'Could not load product.'));
  }, [id]);

  async function addToCart() {
    if (!product) return;
    if (!localStorage.getItem('smart_ecom_token')) {
      window.location.href = `/login?add_product=${product.id}`;
      return;
    }
    try {
      await apiFetch('/api/cart/items', { method: 'POST', body: JSON.stringify({ product: product.id, quantity: 1 }) });
      setMessage('Added to cart.');
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 401) {
        window.location.href = `/login?add_product=${product.id}`;
        return;
      }
      setMessage(error instanceof Error ? error.message : 'Could not add this item.');
    }
  }

  return (
    <main className="page-shell">
      <Navbar />
      {product ? <section className="summary-box">
        <h2>{product.name}</h2>
        {mediaUrl(product.image) && <img className="product-image" src={mediaUrl(product.image) ?? undefined} alt={product.name} />}
        <p>{product.description}</p>
        <p>Price: {formatCurrency(product.price)} | Stock: {product.stock}</p>
        <button type="button" disabled={product.stock < 1} onClick={addToCart}>Add to cart</button>
      </section> : <p role="status">{message}</p>}
      {product && message && <p role="status">{message}</p>}
    </main>
  );
}
