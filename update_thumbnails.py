#!/usr/bin/env python
"""
Update product thumbnails from .avif to .png in the database
Run this after converting images to PNG format
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'naik.settings')
django.setup()

from main.models import Product

def update_product_thumbnails():
    """Update all product thumbnails from .avif to .png"""
    products = Product.objects.all()
    updated_count = 0

    print("Updating product thumbnails...")
    print("=" * 60)

    for product in products:
        if product.thumbnail and product.thumbnail.name.endswith('.avif'):
            old_path = product.thumbnail.name
            new_path = old_path.replace('.avif', '.png')

            product.thumbnail.name = new_path
            product.save()

            print(f"✓ Updated: {product.title}")
            print(f"  {old_path} -> {new_path}")
            updated_count += 1

    print("=" * 60)
    print(f"\nUpdated {updated_count} products")

if __name__ == '__main__':
    update_product_thumbnails()
