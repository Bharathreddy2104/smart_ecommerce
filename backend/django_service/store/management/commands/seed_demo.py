from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
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

# Unsplash photo IDs document the source of each locally bundled product photo.
PRODUCT_PHOTOS = {
    'mens-casual-cotton-shirt': '1516826957135-700dedea698c',
    'mens-slim-fit-jeans': '1542272604-787c3835535d',
    'mens-formal-shirt': '1521572163474-6864f9cf17ab',
    'mens-polo-t-shirt': '1551028719-00167b16eac5',
    'mens-lightweight-hoodie': '1515886657613-9f3515b0c78f',
    'womens-floral-summer-dress': '1515372039744-b8f02a3ae446',
    'womens-casual-kurti': '1529139574466-a303027c1d8b',
    'womens-denim-jacket': '1490481651871-ab68de25d43d',
    'womens-hooded-sweatshirt': '1503342217505-b0a15ec3261c',
    'womens-cotton-leggings': '1483985988355-763728e1935b',
    'womens-running-shoes': '1543163521-1bf539c55dd2',
    'mens-sports-shoes': '1542291026-7eec264c27ff',
    'mens-casual-sneakers': '1549298916-b41d501d3772',
    'womens-casual-sneakers': '1600185365483-26d7a4cc7519',
    'mens-formal-shoes': '1560343090-f0409e92791a',
    'wireless-bluetooth-headphones': '1505740420928-5e560c06d30e',
    'smart-watch': '1523275335684-37898b6baf30',
    'wireless-mouse': '1527814050087-3793815479db',
    'mechanical-keyboard': '1587829741301-dc798b83add3',
    'usb-c-hub': '1498049794561-7780e7231661',
    'bluetooth-speaker': '1590658268037-6bf12165a8df',
    '20000-mah-power-bank': '1583394838336-acd977736f90',
    '5g-android-smartphone': '1511707171634-5f897ff02aa9',
    'protective-smartphone-case': '1598327105666-5b89351aff97',
    'fast-charging-adapter': '1605236453806-6ff36851218e',
    'braided-usb-c-cable': '1592750475338-74b7b21085ab',
    '14-inch-everyday-laptop': '1496181133206-80ce9b88a853',
    '27-inch-full-hd-monitor': '1498050108023-c5249f4df085',
    '1080p-usb-webcam': '1531297484001-80022131f5a1',
    '1-tb-portable-ssd': '1517336714731-489689fd1ca8',
    'adjustable-laptop-stand': '1541807084-5c52b6b3adef',
    'digital-air-fryer': '1556911220-e15b29be8c8f',
    'electric-kettle': '1556910103-1c02745aae4d',
    '750-w-mixer-grinder': '1556909114-f6e7ad7d3136',
    'drip-coffee-maker': '1494438639946-1ebd1d20bf85',
    'non-stick-frying-pan': '1495474472287-4d71bcdd2085',
    'desk-lamp': '1509042239860-f550ce710b93',
    'insulated-bottle': '1608270586620-248524c67de9',
    'daily-face-moisturizer': '1608248543803-ba4f8c70ae0b',
    'spf-50-sunscreen-lotion': '1596462502278-27bfdc403348',
    'floral-eau-de-parfum': '1556229010-6c3f2c9ca5f8',
    'ceramic-hair-dryer': '1570172619644-dfd03ed5d881',
    'stainless-steel-insulated-bottle': '1602143407151-7111542de6e8',
    'aviator-sunglasses': '1511499767150-a48a237f0083',
    'everyday-leather-wallet': '1584917865442-de89df76afd3',
    'travel-backpack': '1553062407-98eeb64c6a62',
    'minimal-analog-watch': '1523170335258-f5ed11844a49',
    'laptop-sleeve': '1544816155-12df9643f363',
}


class Command(BaseCommand):
    help = 'Create an idempotent demo catalog with bundled product photography.'

    def handle(self, *args, **options):
        media_products = Path(settings.MEDIA_ROOT) / 'products'
        media_products.mkdir(parents=True, exist_ok=True)
        product_count = 0

        for category_name, products in CATALOG.items():
            category, _ = Category.objects.get_or_create(name=category_name)
            for name, description, price, stock, popularity, _glyph in products:
                product_slug = slugify(name)
                if product_slug not in PRODUCT_PHOTOS:
                    raise CommandError(f'No product photo is mapped for "{name}".')
                image_name = f'products/{product_slug}.jpg'
                image_path = Path(settings.MEDIA_ROOT) / image_name
                if not image_path.is_file():
                    raise CommandError(f'Bundled product photo is missing: {image_path}')
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
