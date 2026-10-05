import Link from 'next/link';

export default function Navbar() {
  return (
    <nav className="navbar">
      <Link href="/">SmartCart</Link>
      <div className="nav-links">
        <Link href="/products">Products</Link>
        <Link href="/cart">Cart</Link>
        <Link href="/orders">Orders</Link>
        <Link href="/notifications">Notifications</Link>
        <Link href="/profile">Profile</Link>
        <Link href="/login">Login</Link>
        <Link href="/register">Register</Link>
      </div>
    </nav>
  );
}
