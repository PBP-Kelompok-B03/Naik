import os
import django
from datetime import timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'naik.settings')
django.setup()

from django.utils import timezone
from main.models import Product
from django.contrib.auth.models import User

def create_test_auction():
    # Get first user
    user = User.objects.filter(is_active=True).first()
    if not user:
        print('No active users found')
        return

    # Create a test auction
    auction = Product.objects.create(
        user=user,
        title='Test Auction for Bidding',
        price=10000,  # Starting price
        category="Men's Shoes",
        stock=1,
        is_auction=True,
        auction_increment=1000,  # Minimum increment
        auction_end_time=timezone.now() + timedelta(hours=1)  # Ends in 1 hour
    )

    print(f'Created auction: {auction.title} (ID: {auction.id})')
    print(f'Starting price: Rp {auction.price}')
    print(f'Increment: Rp {auction.auction_increment}')
    print(f'Ends at: {auction.auction_end_time}')

    return auction

if __name__ == '__main__':
    create_test_auction()