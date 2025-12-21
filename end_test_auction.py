import os
import django
from datetime import timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'naik.settings')
django.setup()

from django.utils import timezone
from main.models import Product

def end_test_auction():
    # Get the test auction
    product = Product.objects.filter(title='Test Auction for Bidding').first()
    if not product:
        print('Test auction not found')
        return

    # Set end time to past
    product.auction_end_time = timezone.now() - timedelta(minutes=1)
    product.save()

    print(f'Ended auction: {product.title}')
    print(f'New end time: {product.auction_end_time}')

if __name__ == '__main__':
    end_test_auction()