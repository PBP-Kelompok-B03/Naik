from django.core.management.base import BaseCommand
from main.models import Product
from django.conf import settings
import csv, os

class Command(BaseCommand):
    help = 'Import products from CSV using .avif images named 1.avif, 2.avif, etc.'

    def handle(self, *args, **options):
        csv_path = os.path.join(settings.BASE_DIR, 'static', 'data', 'products.csv')

        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(f"❌ CSV file not found at {csv_path}"))
            return

        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            count = 0

            for index, row in enumerate(reader, start=1):
                name = row['Product Name'].strip()
                price = int(row['Price (IDR)'].replace('.', '').strip())
                category = row['Category'].strip()

                # ✅ Use .avif image file for each row number
                thumbnail_path = f"image/products/{index}"

                product, created = Product.objects.get_or_create(
                    title=name,
                    category=category,
                    defaults={
                        'price': price,
                        'thumbnail': thumbnail_path,
                    }
                )

                if created:
                    count += 1

            self.stdout.write(self.style.SUCCESS(f"✅ Successfully imported {count} products with .avif images!"))
