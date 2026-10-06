import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'SmartCart | Thoughtful finds, easy shopping',
  description: 'Discover everyday fashion, technology, home and lifestyle finds at SmartCart.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
