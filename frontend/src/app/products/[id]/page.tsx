'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useParams } from 'next/navigation';
import Navbar from '@/components/Navbar';
import ProductCard from '@/components/ProductCard';
import { ApiRequestError, apiFetch, formatCurrency, mediaUrl } from '@/lib/api';
import { categoryIcon, type Category, type Product } from '@/lib/catalog';

export default function ProductDetailPage() {
  const params = useParams();
  const id = String(params.id);
  const [product, setProduct] = useState<Product | null>(null);
  const [categoryName, setCategoryName] = useState('');
  const [related, setRelated] = useState<Product[]>([]);
  const [quantity, setQuantity] = useState(1);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('Loading product...');

  useEffect(() => {
    let active = true;
    async function loadProduct() {
      try {
        const [item, categories] = await Promise.all([
          apiFetch<Product>(`/api/products/${id}`),
          apiFetch<Category[]>('/api/categories'),
        ]);
        if (!active) return;
        setProduct(item);
        setCategoryName(categories.find((category) => category.id === item.category)?.name ?? '');
        setMessage('');
        if (item.category) {
          const items = await apiFetch<Product[]>(`/api/products?category=${item.category}&sort=popularity`);
          if (active) setRelated(items.filter((relatedItem) => relatedItem.id !== item.id).slice(0, 4));
        }
      } catch (error) {
        if (active) setMessage(error instanceof Error ? error.message : 'Could not load product.');
      }
    }
    void loadProduct();
    return () => { active = false; };
  }, [id]);

  async function addToCart(checkout = false) {
    if (!product) return;
    if (!localStorage.getItem('smart_ecom_token')) {
      const query = new URLSearchParams({
        add_product: String(product.id),
        quantity: String(quantity),
        ...(checkout ? { checkout: '1' } : {}),
      });
      window.location.href = `/login?${query.toString()}`;
      return;
    }
    setBusy(true);
    setMessage('');
    try {
      await apiFetch('/api/cart/items', {
        method: 'POST',
        body: JSON.stringify({ product: product.id, quantity }),
      });
      if (checkout) {
        window.location.href = '/checkout';
        return;
      }
      setMessage('Added to your cart.');
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 401) {
        window.location.href = `/login?add_product=${product.id}&quantity=${quantity}${checkout ? '&checkout=1' : ''}`;
        return;
      }
      setMessage(error instanceof Error ? error.message : 'Could not add this item.');
    } finally {
      setBusy(false);
    }
  }

  const image = mediaUrl(product?.image);

  return (
    <main className="page-shell">
      <Navbar />
      {product ? (
        <>
          <section className="product-detail">
            <div className="detail-image-wrap">
              {image ? (
                <Image className="detail-image" src={image} alt={product.name} fill sizes="(max-width: 700px) 100vw, 50vw" priority unoptimized />
              ) : (
                <div className="product-image-fallback detail-image-fallback" aria-hidden="true">
                  <span>{categoryIcon(categoryName)}</span>
                </div>
              )}
            </div>
            <div className="detail-info">
              {categoryName && <Link href={`/products?category=${product.category}`} className="category-label">{categoryName}</Link>}
              {(product.popularity ?? 0) >= 85 && <span className="popular-label detail-popular">Popular with shoppers</span>}
              <h1>{product.name}</h1>
              <p className="detail-description">{product.description}</p>
              <p className="detail-price">{formatCurrency(product.price)}</p>
              <p className={product.stock > 0 ? 'availability in-stock' : 'availability stock-out'}>
                {product.stock > 0 ? `${product.stock} available` : 'Currently out of stock'}
              </p>
              <div className="detail-meta">
                {categoryName && <span>Category: <strong>{categoryName}</strong></span>}
                <span>Popularity: <strong>{product.popularity ?? 0}</strong></span>
              </div>
              {product.stock > 0 && (
                <>
                  <div className="quantity-picker">
                    <span>Quantity</span>
                    <div className="quantity-control">
                      <button type="button" aria-label="Decrease quantity" disabled={quantity <= 1} onClick={() => setQuantity((value) => Math.max(1, value - 1))}>−</button>
                      <output aria-live="polite">{quantity}</output>
                      <button type="button" aria-label="Increase quantity" disabled={quantity >= product.stock} onClick={() => setQuantity((value) => Math.min(product.stock, value + 1))}>+</button>
                    </div>
                  </div>
                  <div className="detail-actions">
                    <button type="button" className="primary-btn" disabled={busy} onClick={() => void addToCart()}>
                      {busy ? 'Adding...' : 'Add to cart'}
                    </button>
                    <button type="button" className="secondary-btn" disabled={busy} onClick={() => void addToCart(true)}>
                      Buy now
                    </button>
                  </div>
                </>
              )}
              {message && <p className="inline-status" role="status">{message}</p>}
              <p className="muted detail-delivery">Secure checkout · Order updates in your account</p>
            </div>
          </section>
          {related.length > 0 && (
            <section className="section-block">
              <div className="section-heading">
                <div><p className="eyebrow">A few more to love</p><h2>Related products</h2></div>
                {product.category && <Link href={`/products?category=${product.category}`} className="section-link">Shop this category <span aria-hidden="true">→</span></Link>}
              </div>
              <div className="card-grid">
                {related.map((item) => <ProductCard key={item.id} product={item} categoryLabel={categoryName} />)}
              </div>
            </section>
          )}
        </>
      ) : (
        <p className="page-status" role="status">{message}</p>
      )}
    </main>
  );
}
