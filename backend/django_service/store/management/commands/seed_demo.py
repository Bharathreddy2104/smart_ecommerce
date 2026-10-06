from html import escape
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from store.models import Category, Product


CATALOG = {
    "Men's Clothing": [
        ('Men’s Casual Cotton Shirt', 'Breathable cotton shirt with a relaxed everyday fit.', '1299.00', 24, 88, '👔'),
        ('Men’s Slim Fit Jeans', 'Stretch denim jeans with a clean slim silhouette.', '1899.00', 18, 82, '👖'),
        ('Men’s Formal Shirt', 'Crisp wrinkle-resistant shirt for work and occasions.', '1599.00', 15, 75, '👔'),
        ('Men’s Polo T-Shirt', 'Soft pique cotton polo with a classic collar.', '999.00', 32, 69, '👕'),
        ('Men’s Lightweight Hoodie', 'Midweight fleece hoodie for cool mornings and evenings.', '1799.00', 13, 61, '🧥'),
    ],
    "Women's Clothing": [
        ('Women’s Floral Summer Dress', 'Airy floral-print dress made for warm-weather outings.', '2199.00', 17, 96, '👗'),
        ('Women’s Casual Kurti', 'Comfortable printed kurti with an easy straight fit.', '1199.00', 26, 91, '👚'),
        ('Women’s Denim Jacket', 'Classic mid-wash denim jacket with functional pockets.', '2499.00', 11, 77, '🧥'),
        ('Women’s Hooded Sweatshirt', 'Soft brushed-fleece sweatshirt with an adjustable hood.', '1699.00', 20, 72, '🧥'),
        ('Women’s Cotton Leggings', 'Stretch cotton leggings for everyday comfort.', '699.00', 38, 64, '👖'),
    ],
    'Shoes': [
        ('Women’s Running Shoes', 'Lightweight cushioned trainers for daily runs and walks.', '2899.00', 14, 95, '👟'),
        ('Men’s Sports Shoes', 'Breathable mesh sports shoes with a grippy sole.', '3199.00', 12, 89, '👟'),
        ('Men’s Casual Sneakers', 'Versatile low-top sneakers for everyday wear.', '2499.00', 21, 83, '👟'),
        ('Women’s Casual Sneakers', 'Everyday lace-up sneakers with a cushioned footbed.', '2299.00', 16, 74, '👟'),
        ('Men’s Formal Shoes', 'Polished lace-up shoes with a comfortable lining.', '3599.00', 9, 67, '👞'),
    ],
    'Electronics': [
        ('Wireless Bluetooth Headphones', 'Over-ear wireless headphones with a foldable design.', '3499.00', 18, 98, '🎧'),
        ('Smart Watch', 'Fitness-ready smart watch with activity and sleep tracking.', '4299.00', 16, 93, '⌚'),
        ('Wireless Mouse', 'Compact wireless mouse with adjustable sensitivity.', '899.00', 34, 87, '🖱️'),
        ('Mechanical Keyboard', 'Tactile mechanical keyboard for work and gaming.', '3299.00', 12, 84, '⌨️'),
        ('USB-C Hub', 'Multiport USB-C hub with HDMI and USB connectivity.', '1899.00', 22, 76, '🔌'),
        ('Bluetooth Speaker', 'Portable Bluetooth speaker with clear stereo sound.', '2199.00', 19, 71, '🔊'),
        ('20,000 mAh Power Bank', 'High-capacity portable power bank with USB-C output.', '1599.00', 27, 79, '🔋'),
    ],
    'Mobiles & Accessories': [
        ('5G Android Smartphone', 'Unlocked 5G smartphone with a bright full-view display.', '18999.00', 10, 99, '📱'),
        ('Protective Smartphone Case', 'Shock-absorbing case with a raised camera rim.', '499.00', 46, 85, '📱'),
        ('Fast Charging Adapter', 'Compact 30 W USB-C adapter for compatible devices.', '999.00', 30, 80, '🔌'),
        ('Braided USB-C Cable', 'Durable 1.5 m braided cable for charging and data.', '349.00', 52, 73, '🔌'),
    ],
    'Laptops & Computers': [
        ('14-inch Everyday Laptop', 'Portable laptop configured for study, work, and browsing.', '52999.00', 7, 94, '💻'),
        ('27-inch Full HD Monitor', 'Slim-bezel monitor for a comfortable home-office setup.', '12999.00', 8, 81, '🖥️'),
        ('1080p USB Webcam', 'Plug-and-play webcam with an adjustable privacy cover.', '2499.00', 15, 68, '📷'),
        ('1 TB Portable SSD', 'Pocket-sized solid-state drive for fast file transfers.', '6999.00', 11, 78, '💾'),
        ('Adjustable Laptop Stand', 'Foldable aluminum stand with multiple viewing angles.', '1499.00', 20, 66, '💻'),
    ],
    'Home & Kitchen': [
        ('Digital Air Fryer', 'Compact air fryer with a simple digital control panel.', '6499.00', 9, 92, '🍟'),
        ('Electric Kettle', '1.5 L stainless-steel kettle with automatic shut-off.', '1499.00', 24, 86, '🫖'),
        ('750 W Mixer Grinder', 'Three-jar mixer grinder for everyday kitchen prep.', '3499.00', 13, 83, '🥣'),
        ('Drip Coffee Maker', 'Countertop coffee maker with a reusable filter basket.', '2799.00', 10, 70, '☕'),
        ('Non-stick Frying Pan', 'Induction-compatible frying pan with a stay-cool handle.', '1199.00', 17, 62, '🍳'),
    ],
    'Home': [
        ('Desk Lamp', 'Adjustable LED desk lamp with warm and cool settings.', '32.00', 14, 58, '💡'),
        ('Insulated Bottle', 'Reusable stainless steel bottle for hot or cold drinks.', '18.75', 4, 51, '🥤'),
    ],
    'Beauty': [
        ('Daily Face Moisturizer', 'Lightweight daily moisturizer for soft, hydrated skin.', '599.00', 36, 90, '🧴'),
        ('SPF 50 Sunscreen Lotion', 'Broad-spectrum sunscreen lotion for daily outdoor use.', '749.00', 29, 88, '🧴'),
        ('Floral Eau de Parfum', 'Fresh floral fragrance in a travel-friendly glass bottle.', '1999.00', 14, 76, '🧴'),
        ('Ceramic Hair Dryer', 'Compact hair dryer with two heat settings and a cool-air mode.', '1799.00', 12, 65, '💨'),
    ],
    'Accessories': [
        ('Stainless Steel Insulated Bottle', 'Reusable insulated bottle for hot or cold drinks.', '899.00', 31, 75, '🧴'),
        ('Aviator Sunglasses', 'Lightweight UV-protective sunglasses with a classic frame.', '1299.00', 22, 63, '🕶️'),
        ('Everyday Leather Wallet', 'Slim wallet with card slots and a secure bill pocket.', '999.00', 18, 60, '👛'),
        ('Travel Backpack', 'Roomy everyday backpack with padded laptop storage.', '2499.00', 16, 72, '🎒'),
        ('Minimal Analog Watch', 'Clean analog watch with a comfortable everyday strap.', '2299.00', 13, 58, '⌚'),
        ('Laptop Sleeve', 'Padded sleeve for a 14-inch laptop.', '27.25', 20, 43, '💻'),
    ],
}

CATEGORY_COLORS = {
    "Men's Clothing": ('#dbeafe', '#1d4ed8'),
    "Women's Clothing": ('#fce7f3', '#be185d'),
    'Shoes': ('#ffedd5', '#c2410c'),
    'Electronics': ('#e0e7ff', '#4338ca'),
    'Mobiles & Accessories': ('#cffafe', '#0e7490'),
    'Laptops & Computers': ('#dbeafe', '#0369a1'),
    'Home & Kitchen': ('#dcfce7', '#15803d'),
    'Home': ('#dcfce7', '#15803d'),
    'Beauty': ('#fae8ff', '#a21caf'),
    'Accessories': ('#fef3c7', '#b45309'),
}


def product_artwork(name, glyph, background, accent):
    safe_name = escape(name)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 520" role="img" aria-label="{safe_name}">
  <defs>
    <linearGradient id="wash" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{background}"/>
      <stop offset="1" stop-color="#ffffff"/>
    </linearGradient>
  </defs>
  <rect width="640" height="520" rx="36" fill="url(#wash)"/>
  <circle cx="320" cy="225" r="148" fill="#ffffff" opacity=".78"/>
  <circle cx="320" cy="225" r="123" fill="{background}"/>
  <path d="M112 382h416" stroke="{accent}" stroke-width="3" opacity=".18"/>
  <text x="320" y="275" text-anchor="middle" font-size="150" font-family="Segoe UI Emoji, Apple Color Emoji, sans-serif">{glyph}</text>
  <rect x="95" y="404" width="450" height="62" rx="18" fill="#ffffff" opacity=".88"/>
  <text x="320" y="443" text-anchor="middle" font-size="21" font-family="Arial, sans-serif" font-weight="700" fill="#172033">{safe_name}</text>
</svg>
'''


class Command(BaseCommand):
    help = 'Create an idempotent demo catalog with locally generated product artwork.'

    def handle(self, *args, **options):
        media_products = Path(settings.MEDIA_ROOT) / 'products'
        media_products.mkdir(parents=True, exist_ok=True)
        product_count = 0

        for category_name, products in CATALOG.items():
            category, _ = Category.objects.get_or_create(name=category_name)
            background, accent = CATEGORY_COLORS[category_name]
            for name, description, price, stock, popularity, glyph in products:
                image_name = f'products/{slugify(name)}.svg'
                image_path = Path(settings.MEDIA_ROOT) / image_name
                image_path.parent.mkdir(parents=True, exist_ok=True)
                image_path.write_text(
                    product_artwork(name, glyph, background, accent),
                    encoding='utf-8',
                )
                Product.objects.update_or_create(
                    name=name,
                    defaults={
                        'description': description,
                        'price': price,
                        'stock': stock,
                        'popularity': popularity,
                        'category': category,
                        'image': image_name,
                    },
                )
                product_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Demo catalog is ready: {product_count} products across {len(CATALOG)} categories.'
            )
        )
