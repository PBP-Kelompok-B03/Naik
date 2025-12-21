import requests
import json
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'naik.settings')
django.setup()

from main.models import Product

# Test bidding API
def test_place_bid():
    # Get the test auction we just created
    try:
        product = Product.objects.filter(title='Test Auction for Bidding').first()
        if not product:
            print('Test auction not found')
            return

        print(f'Testing bid on product: {product.title} (ID: {product.id})')

        url = f'http://127.0.0.1:8000/auction/api/bid/{product.id}/'

        # Test data - bid higher than current price
        bid_data = {
            'amount': '16000'  # Bid at minimum required amount
        }

        print(f'Posting bid: {bid_data}')

        response = requests.post(url, data=bid_data)
        print('Status:', response.status_code)
        try:
            print('Response:', response.json())
        except:
            print('Response text:', response.text)

    except Exception as e:
        print('Error:', e)

if __name__ == '__main__':
    test_place_bid()

if __name__ == '__main__':
    test_place_bid()