'use client';

import { useEffect, useState } from 'react';
import Navbar from '@/components/Navbar';
import ProductCard from '@/components/ProductCard';
import { apiFetch } from '@/lib/api';

type Product = { id: number; name: string; description: string; price: number; stock: number; image?: string | null };
type Category = { id: number; name: string };

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [filters, setFilters] = useState({ q: '', category: '', min_price: '', max_price: '', sort: 'popularity' });
  const [message, setMessage] = useState('Loading products...');

  useEffect(() => {
    let active = true;
    const query = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => { if (value) query.set(key, value); });
    Promise.all([
      apiFetch<Product[]>(`/api/products?${query.toString()}`),
      apiFetch<Category[]>('/api/categories'),
    ]).then(([items, categoryItems]) => {
      if (!active) return;
      setProducts(items);
      setCategories(categoryItems);
      setMessage(items.length ? '' : 'No products match these filters.');
    }).catch((error: unknown) => {
      if (active) setMessage(error instanceof Error ? error.message : 'Could not load products.');
    });
    return () => { active = false; };
  }, [filters]);

  function updateFilter(key: keyof typeof filters, value: string) {
    setFilters((current) => ({ ...current, [key]: value }));
  }

  return (
    <main className="page-shell">
      <Navbar />
      <h2>Products</h2>
      <section className="filter-row" aria-label="Product filters">
        <input aria-label="Search products" placeholder="Search" value={filters.q} onChange={(event) => updateFilter('q', event.target.value)} />
        <select aria-label="Category" value={filters.category} onChange={(event) => updateFilter('category', event.target.value)}>
          <option value="">All categories</option>
          {categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}
        </select>
        <input aria-label="Minimum price" type="number" min="0" placeholder="Min price" value={filters.min_price} onChange={(event) => updateFilter('min_price', event.target.value)} />
        <input aria-label="Maximum price" type="number" min="0" placeholder="Max price" value={filters.max_price} onChange={(event) => updateFilter('max_price', event.target.value)} />
        <select aria-label="Sort products" value={filters.sort} onChange={(event) => updateFilter('sort', event.target.value)}>
          <option value="popularity">Popularity</option>
          <option value="price_asc">Price: low to high</option>
          <option value="price_desc">Price: high to low</option>
          <option value="newest">Newest</option>
        </select>
      </section>
      {message && <p role="status">{message}</p>}
      <div className="card-grid">
        {products.map((product) => (
          <ProductCard key={product.id} product={{ ...product, price: Number(product.price) }} />
        ))}
      </div>
    </main>
  );
}
