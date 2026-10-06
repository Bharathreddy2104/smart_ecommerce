'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import Navbar from '@/components/Navbar';
import ProductCard from '@/components/ProductCard';
import { apiFetch } from '@/lib/api';
import { categoryIcon, type Category, type Product } from '@/lib/catalog';

const categoryDescriptions: Record<string, string> = {
  Accessories: 'The little details that make a difference.',
  Beauty: 'Everyday care and feel-good essentials.',
  'Home & Kitchen': 'Useful upgrades for your favorite spaces.',
  'Laptops & Computers': 'Tools for work, study and play.',
  'Men’s Clothing': 'Easy-to-wear styles for every day.',
  'Mobiles & Accessories': 'Keep your devices ready for anything.',
  Shoes: 'Comfort and style, step after step.',
  'Women’s Clothing': 'Fresh styles for everyday moments.',
};

export default function HomePage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [popular, setPopular] = useState<Product[]>([]);
  const [newArrivals, setNewArrivals] = useState<Product[]>([]);
  const [message, setMessage] = useState('');

  useEffect(() => {
    let active = true;
    Promise.all([
      apiFetch<Category[]>('/api/categories'),
      apiFetch<Product[]>('/api/products?sort=popularity'),
      apiFetch<Product[]>('/api/products?sort=newest'),
    ]).then(([categoryItems, popularItems, newestItems]) => {
      if (!active) return;
      setCategories(categoryItems);
      setPopular(popularItems.slice(0, 8));
      setNewArrivals(newestItems.slice(0, 8));
    }).catch((error: unknown) => {
      if (active) setMessage(error instanceof Error ? error.message : 'Could not load the storefront catalog.');
    });
    return () => { active = false; };
  }, []);

  const categoryNames = new Map(categories.map((category) => [category.id, category.name]));
  const affordableFinds = popular.filter((product) => Number(product.price) <= 2000).slice(0, 4);

  return (
    <main className="page-shell">
      <Navbar />
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">A little smarter shopping</p>
          <h1>Good things for every day.</h1>
          <p className="subtext">Find thoughtful picks for your wardrobe, workspace and home — all in one easy place.</p>
          <div className="hero-actions">
            <Link href="/products" className="primary-btn">Explore the collection</Link>
            <Link href="/#categories" className="secondary-btn">Shop by category</Link>
          </div>
          <div className="hero-promises">
            <span>✓ Curated everyday picks</span>
            <span>✓ Secure checkout</span>
            <span>✓ Easy order tracking</span>
          </div>
        </div>
        <div className="hero-art" aria-hidden="true">
          <span className="hero-orbit orbit-one" />
          <span className="hero-orbit orbit-two" />
          <span className="hero-bag">🛍️</span>
          <span className="hero-spark spark-one">✦</span>
          <span className="hero-spark spark-two">✧</span>
          <span className="hero-note">Find your<br />next favorite</span>
        </div>
      </section>

      <section className="section-block" id="categories">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Find your thing</p>
            <h2>Shop by category</h2>
          </div>
          <Link href="/products" className="section-link">View everything <span aria-hidden="true">→</span></Link>
        </div>
        <div className="category-grid">
          {categories.map((category) => (
            <Link className="category-card" href={`/products?category=${category.id}`} key={category.id}>
              <span className="category-icon" aria-hidden="true">{categoryIcon(category.name)}</span>
              <span className="category-name">{category.name}</span>
              <span className="category-description">{categoryDescriptions[category.name] ?? 'Explore the latest collection.'}</span>
              <span className="category-arrow" aria-hidden="true">↗</span>
            </Link>
          ))}
        </div>
      </section>

      {message && <p className="page-status" role="status">{message}</p>}

      <section className="section-block">
        <div className="section-heading">
          <div>
            <p className="eyebrow">A good place to start</p>
            <h2>Featured products</h2>
          </div>
          <Link href="/products?sort=popularity" className="section-link">See all featured <span aria-hidden="true">→</span></Link>
        </div>
        <div className="card-grid">
          {popular.slice(0, 4).map((product) => (
            <ProductCard key={product.id} product={product} categoryLabel={categoryNames.get(product.category ?? -1)} />
          ))}
        </div>
      </section>

      <section className="section-block">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Loved by shoppers</p>
            <h2>Popular right now</h2>
          </div>
          <Link href="/products?sort=popularity" className="section-link">See popular picks <span aria-hidden="true">→</span></Link>
        </div>
        <div className="card-grid">
          {popular.slice(4, 8).map((product) => (
            <ProductCard key={product.id} product={product} categoryLabel={categoryNames.get(product.category ?? -1)} />
          ))}
        </div>
      </section>

      {affordableFinds.length > 0 && (
        <section className="offer-banner">
          <div>
            <p className="eyebrow">Smart finds under ₹2,000</p>
            <h2>Little upgrades, lovely prices.</h2>
            <p>A few customer favorites that are easy on the budget.</p>
          </div>
          <Link href="/products?max_price=2000" className="secondary-btn">Explore under ₹2,000</Link>
        </section>
      )}

      <section className="section-block">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Just added</p>
            <h2>New arrivals</h2>
          </div>
          <Link href="/products?sort=newest" className="section-link">Discover more <span aria-hidden="true">→</span></Link>
        </div>
        <div className="card-grid">
          {newArrivals.slice(0, 4).map((product) => (
            <ProductCard key={product.id} product={product} categoryLabel={categoryNames.get(product.category ?? -1)} />
          ))}
        </div>
      </section>

      <footer className="site-footer">
        <Link href="/">SmartCart</Link>
        <span>Thoughtful finds. Easy shopping.</span>
        <div><Link href="/products">Shop</Link><Link href="/orders">Orders</Link><Link href="/profile">Your profile</Link></div>
      </footer>
    </main>
  );
}
