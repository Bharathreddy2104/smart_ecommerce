'use client';

import { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { ApiRequestError, apiFetch, formatCurrency, mediaUrl } from '@/lib/api';
import { categoryIcon, type Product } from '@/lib/catalog';

export default function ProductCard({
  product,
  categoryLabel,
}: {
  product: Product;
  categoryLabel?: string;
}) {
  const [message, setMessage] = useState('');
  const image = mediaUrl(product.image);

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
      setMessage('Added to your cart.');
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 401) {
        window.location.href = `/login?add_product=${product.id}`;
        return;
      }
      setMessage(error instanceof Error ? error.message : 'Could not add this item.');
    }
  }

  return (
    <article className="product-card">
      <Link href={`/products/${product.id}`} className="product-art-link" aria-label={`View ${product.name}`}>
        {image ? (
          <Image
            className="product-image"
            src={image}
            alt={product.name}
            fill
            sizes="(max-width: 700px) 50vw, (max-width: 980px) 33vw, 25vw"
            unoptimized
          />
        ) : (
          <div className="product-image-fallback" aria-hidden="true">
            <span>{categoryIcon(categoryLabel ?? '')}</span>
          </div>
        )}
      </Link>
      <div className="product-card-content">
        <div className="product-card-meta">
          {categoryLabel && <span className="category-label">{categoryLabel}</span>}
          {(product.popularity ?? 0) >= 85 && <span className="popular-label">Popular</span>}
        </div>
        <h3><Link href={`/products/${product.id}`}>{product.name}</Link></h3>
        <p className="product-description">{product.description}</p>
        <div className="product-purchase-row">
          <span className="price">{formatCurrency(product.price)}</span>
          <span className={product.stock > 0 ? 'stock-label' : 'stock-label stock-out'}>
            {product.stock > 0 ? `${product.stock} in stock` : 'Out of stock'}
          </span>
        </div>
        <div className="product-actions">
          <Link href={`/products/${product.id}`} className="secondary-btn">View details</Link>
          <button type="button" className="primary-btn" disabled={product.stock < 1} onClick={addToCart}>
            Add to cart
          </button>
        </div>
        {message && <p className="inline-status" role="status">{message}</p>}
      </div>
    </article>
  );
}
