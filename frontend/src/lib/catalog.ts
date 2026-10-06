export type Product = {
  id: number;
  name: string;
  description: string;
  price: number | string;
  stock: number;
  image?: string | null;
  category?: number | null;
  popularity?: number;
};

export type Category = {
  id: number;
  name: string;
  description?: string;
};

export function categoryIcon(name: string): string {
  const category = name.toLowerCase();
  if (category.includes('shoe')) return '👟';
  if (category.includes('women')) return '👗';
  if (category.includes('men')) return '👔';
  if (category.includes('beauty')) return '🧴';
  if (category.includes('home') || category.includes('kitchen')) return '🍳';
  if (category.includes('mobile')) return '📱';
  if (category.includes('laptop') || category.includes('computer')) return '💻';
  if (category.includes('electronic')) return '🎧';
  if (category.includes('accessor')) return '🎒';
  if (category.includes('fashion')) return '🛍️';
  return '✨';
}
