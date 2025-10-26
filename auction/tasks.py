from django.utils import timezone
from main.models import Product
from django.shortcuts import redirect
from django.urls import reverse

def check_auction_end():
    ended_auctions = Product.objects.filter(
        is_auction=True,
        auction_end_time__lte=timezone.now(),
        auction_winner__isnull=True
    )
    
    for product in ended_auctions:
        # Get highest bidder
        highest_bid = product.bids.order_by('-amount').first()
        if highest_bid:
            product.auction_winner = highest_bid.user
            product.save()
            
            # Redirect winner to checkout
            return redirect(reverse('checkout:checkout_view') + 
                          f'?product_id={product.id}&quantity=1')