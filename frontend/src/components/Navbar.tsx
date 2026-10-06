import Link from 'next/link';

export default function Navbar() {
  return (
    <header className="site-header">
      <div className="header-main">
        <Link href="/" className="brand" aria-label="SmartCart home">
          <span className="brand-mark" aria-hidden="true">S</span>
          <span>Smart<span>Cart</span></span>
        </Link>
        <form className="header-search" action="/products" method="get" role="search">
          <label className="sr-only" htmlFor="site-search">Search products</label>
          <input id="site-search" name="q" placeholder="Search for products, brands and more" />
          <button type="submit" aria-label="Search">⌕</button>
        </form>
        <div className="header-account-links">
          <Link href="/login">Log in</Link>
          <Link href="/register" className="header-register">Sign up</Link>
        </div>
      </div>
      <nav className="navbar" aria-label="Main navigation">
        <div className="nav-links">
          <Link href="/products">Shop</Link>
          <Link href="/#categories">Categories</Link>
          <Link href="/orders">Orders</Link>
          <Link href="/notifications">Notifications</Link>
          <Link href="/profile">Profile</Link>
        </div>
        <Link href="/cart" className="cart-link"><span aria-hidden="true">🛒</span> Cart</Link>
      </nav>
    </header>
  );
}
