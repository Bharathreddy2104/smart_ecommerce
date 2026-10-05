from django.core.management.base import BaseCommand

from store.models import Category, Product


class Command(BaseCommand):
    help = 'Create a small repeatable product catalog for project demonstrations.'

    def handle(self, *args, **options):
        catalog = {
            'Electronics': [
                ('Wireless Mouse', 'Compact wireless mouse with adjustable sensitivity.', '24.99', 18, 95),
                ('USB-C Hub', 'Multiport hub for USB-C laptops.', '39.50', 12, 82),
                ('Mechanical Keyboard', 'Compact mechanical keyboard for everyday work.', '69.00', 8, 76),
            ],
            'Home': [
                ('Desk Lamp', 'Adjustable LED desk lamp with warm and cool settings.', '32.00', 14, 58),
                ('Insulated Bottle', 'Reusable stainless steel bottle for hot or cold drinks.', '18.75', 4, 51),
            ],
            'Accessories': [
                ('Laptop Sleeve', 'Padded sleeve for a 14-inch laptop.', '27.25', 20, 43),
            ],
        }
        for category_name, products in catalog.items():
            category, _ = Category.objects.get_or_create(name=category_name)
            for name, description, price, stock, popularity in products:
                Product.objects.update_or_create(
                    name=name,
                    defaults={
                        'description': description,
                        'price': price,
                        'stock': stock,
                        'popularity': popularity,
                        'category': category,
                    },
                )
        self.stdout.write(self.style.SUCCESS('Demo catalog is ready.'))
