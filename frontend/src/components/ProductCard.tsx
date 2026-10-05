'use client';

import { useState } from 'react';
import Link from 'next/link';
import { ApiRequestError, apiFetch, formatCurrency, mediaUrl } from '@/lib/api';

export type ProductCardItem = {
  id: number;
  name: string;
  description: string;
  price: number;
  stock: number;
  image?: string | null;
};

export default function ProductCard({ product }: { product: ProductCardItem }) {
  const [message, setMessage] = useState('');

  async function addToCart() {
    if (!localStorage.getItem('smart_ecom_token')) {
      window.location.href = `/login?add_product=${product.id}`;
      return;
    }
    try {
      await apiFetch('/api/cart/items', {
        method: 'POST',
        body: JSON.stringify({ product: product.id, quantity: 1 }),
      });
      setMessage('Added to cart');
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 401) {
        window.location.href = `/login?add_product=${product.id}`;
        return;
      }
      setMessage(error instanceof Error ? error.message : 'Could not add this item.');
    }
  }

  return (
    <div className="product-card">
      {mediaUrl(product.image) && <img className="product-image" src={mediaUrl(product.image) ?? undefined} alt={product.name} />}
      <div className="price">{formatCurrency(product.price)}</div>
      <h3>{product.name}</h3>
      <p>{product.description}</p>
      <p>Stock: {product.stock}</p>
      <Link href={`/products/${product.id}`} className="primary-btn">View</Link>
      <button type="button" className="secondary-btn" disabled={product.stock < 1} onClick={addToCart}>Add to cart</button>
      {message && <p role="status">{message}</p>}
    </div>
  );
}
