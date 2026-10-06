'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import Navbar from '@/components/Navbar';
import ProductCard from '@/components/ProductCard';
import { apiFetch } from '@/lib/api';
import type { Category, Product } from '@/lib/catalog';

type Filters = {
  q: string;
  category: string;
  min_price: string;
  max_price: string;
  sort: string;
};

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [filters, setFilters] = useState<Filters>({
    q: '',
    category: '',
    min_price: '',
    max_price: '',
    sort: 'popularity',
  });
  const [message, setMessage] = useState('Loading products...');
  const [categoryMessage, setCategoryMessage] = useState('');

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setFilters((current) => ({
      ...current,
      q: params.get('q') ?? current.q,
      category: params.get('category') ?? current.category,
      min_price: params.get('min_price') ?? current.min_price,
      max_price: params.get('max_price') ?? current.max_price,
      sort: params.get('sort') ?? current.sort,
    }));
  }, []);

  useEffect(() => {
    let active = true;
    apiFetch<Category[]>('/api/categories')
      .then((items) => {
        if (active) setCategories(items);
      })
      .catch((error: unknown) => {
        if (active) setCategoryMessage(error instanceof Error ? error.message : 'Could not load categories.');
      });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    let active = true;
    const timeout = window.setTimeout(() => {
      const query = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value) query.set(key, value);
      });
      setMessage('Loading products...');
      apiFetch<Product[]>(`/api/products?${query.toString()}`)
        .then((items) => {
          if (!active) return;
          setProducts(items);
          setMessage(items.length ? '' : 'No products match these filters.');
        })
        .catch((error: unknown) => {
          if (active) setMessage(error instanceof Error ? error.message : 'Could not load products.');
        });
    }, 200);
    return () => {
      active = false;
      window.clearTimeout(timeout);
    };
  }, [filters]);

  function updateFilter(key: keyof Filters, value: string) {
    setFilters((current) => ({ ...current, [key]: value }));
  }

  function clearFilters() {
    setFilters({ q: '', category: '', min_price: '', max_price: '', sort: 'popularity' });
  }

  const categoryNames = new Map(categories.map((category) => [category.id, category.name]));

  return (
    <main className="page-shell">
      <Navbar />
      <section className="catalog-heading">
        <div>
          <p className="eyebrow">Thoughtful finds, all in one place</p>
          <h1>Shop the collection</h1>
          <p>Explore everyday essentials across fashion, tech, home and more.</p>
        </div>
        <span className="catalog-count">{products.length} items</span>
      </section>
      <section className="filter-panel" aria-label="Product filters">
        <div className="filter-row">
          <label className="filter-search">
            <span>Search</span>
            <input
              aria-label="Search products"
              placeholder="Product name or keyword"
              value={filters.q}
              onChange={(event) => updateFilter('q', event.target.value)}
            />
          </label>
          <label>
            <span>Category</span>
            <select aria-label="Category" value={filters.category} onChange={(event) => updateFilter('category', event.target.value)}>
              <option value="">All categories</option>
              {categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}
            </select>
          </label>
          <label>
            <span>Min price (₹)</span>
            <input aria-label="Minimum price" type="number" min="0" placeholder="Any" value={filters.min_price} onChange={(event) => updateFilter('min_price', event.target.value)} />
          </label>
          <label>
            <span>Max price (₹)</span>
            <input aria-label="Maximum price" type="number" min="0" placeholder="Any" value={filters.max_price} onChange={(event) => updateFilter('max_price', event.target.value)} />
          </label>
          <label>
            <span>Sort by</span>
            <select aria-label="Sort products" value={filters.sort} onChange={(event) => updateFilter('sort', event.target.value)}>
              <option value="popularity">Most popular</option>
              <option value="price_asc">Price: low to high</option>
              <option value="price_desc">Price: high to low</option>
              <option value="newest">Newest arrivals</option>
            </select>
          </label>
        </div>
        <button type="button" className="text-button" onClick={clearFilters}>Clear filters</button>
      </section>
      {categoryMessage && <p className="page-status" role="alert">{categoryMessage}</p>}
      {message && <p className="page-status" role="status">{message}</p>}
      <div className="card-grid">
        {products.map((product) => (
          <ProductCard key={product.id} product={product} categoryLabel={categoryNames.get(product.category ?? -1)} />
        ))}
      </div>
      <footer className="site-footer">
        <Link href="/#categories">Browse categories</Link>
        <span>SmartCart · Shopping made a little smarter.</span>
      </footer>
    </main>
  );
}
