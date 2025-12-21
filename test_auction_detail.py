import requests
import json
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'naik.settings')
django.setup()

from main.models import Product

# Test auction detail API
def test_auction_detail():
    # Get the test auction
    try:
        product = Product.objects.filter(title='Test Auction for Bidding').first()
        if not product:
            print('Test auction not found')
            return

        print(f'Testing auction detail for: {product.title} (ID: {product.id})')

        url = f'http://127.0.0.1:8000/auction/api/product/{product.id}/'

        response = requests.get(url)
        print('Status:', response.status_code)
        if response.status_code == 200:
            data = response.json()
            print('Auction Active:', data.get('auction_active'))
            print('Current Highest Bid:', data.get('current_highest_bid'))
            print('Min Bid:', data.get('min_bid'))
            print('Is Winner:', data.get('is_winner'))
            print('Number of bids:', len(data.get('bids', [])))
        else:
            print('Response:', response.text)

    except Exception as e:
        print('Error:', e)

if __name__ == '__main__':
    test_auction_detail()