import Link from 'next/link';

export default function HomePage() {
  return (
    <main className="page-shell">
      <section className="hero">
        <div>
          <p className="eyebrow">Smart E-Commerce Platform</p>
          <h1>Shop smarter. Manage orders better.</h1>
          <p className="subtext">Modern storefront built for customers, admin operations, and a shared MySQL backend.</p>
          <div className="hero-actions">
            <Link href="/products" className="primary-btn">Browse products</Link>
            <Link href="/login" className="secondary-btn">Login</Link>
          </div>
        </div>
      </section>
      <section className="feature-grid">
        <div className="feature-card">
          <h3>Fast customer APIs</h3>
          <p>Secure auth, product search, cart operations, and order management.</p>
        </div>
        <div className="feature-card">
          <h3>Django admin</h3>
          <p>Manage catalog, users, payments, and order workflows in one system.</p>
        </div>
        <div className="feature-card">
          <h3>MySQL foundation</h3>
          <p>Shared database layer with migration ownership kept inside Django.</p>
        </div>
      </section>
    </main>
  );
}
