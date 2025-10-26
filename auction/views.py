from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Max
from decimal import Decimal, InvalidOperation
from main.models import Product
from .models import Bid
from django.urls import reverse

@login_required
def auction_list(request):
    # Get all products that are auctions
    auctions = Product.objects.filter(is_auction=True).order_by('-auction_end_time')
    
    for auction in auctions:
        # Get current highest bid for each auction
        highest_bid = auction.bids.aggregate(Max('amount'))['amount__max']
        auction.current_bid = highest_bid if highest_bid else auction.price
        
        # Check if auction is still active
        auction.is_active = auction.auction_end_time > timezone.now() if auction.auction_end_time else False

    return render(request, 'auction/auction_list.html', {
        'auctions': auctions
    })

@login_required
def auction_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_auction=True)
    bids = Bid.objects.filter(product=product).order_by('-amount')
    now = timezone.now()

    # Initialize variables with default values
    current_highest = Decimal('0')
    min_bid = Decimal('0')
    highest_bid = None
    is_winner = False
    checkout_url = ''
    auction_active = False

    try:
        # Convert bids queryset to list and handle decimal conversion
        bids_list = []
        for bid in bids:
            try:
                amount = Decimal(str(bid.amount))
                bid.amount = amount
                bids_list.append(bid)
            except (InvalidOperation, ValueError):
                continue
        
        bids = bids_list  # Replace queryset with sanitized list
        
        # Get highest bid and calculate values
        highest_bid = bids[0] if bids else None
        current_highest = Decimal(str(highest_bid.amount)) if highest_bid else Decimal(str(product.price))

        # min bid (safe fallback)
        increment = Decimal(str(product.auction_increment)) if product.auction_increment is not None else Decimal('1')
        min_bid = current_highest + increment

        # Check if auction is active
        auction_active = product.auction_end_time > now if product.auction_end_time else False

        # determine winner after auction ends
        if not auction_active:
            # prefer explicit auction_winner, fallback to highest_bid.user
            winner_user = product.auction_winner or (highest_bid.user if highest_bid else None)
            if winner_user and request.user.is_authenticated and winner_user == request.user:
                is_winner = True
                checkout_url = reverse('checkout:checkout_view') + f'?product_id={product.id}&quantity=1'

    except (InvalidOperation, AttributeError, ValueError):
        # Fallback to product price if there's any decimal conversion error
        current_highest = Decimal('0')
        min_bid = Decimal(str(product.price))
        bids = []  # Empty list if there's an error

    context = {
        'product': product,
        'bids': bids,
        'current_time': now,
        'current_highest_bid': current_highest,
        'min_bid': min_bid,
        'auction_active': auction_active,
        'is_winner': is_winner,
        'checkout_url': checkout_url,
    }

    return render(request, "auction/auction_detail.html", context)

@login_required
def create_auction(request):
    if request.method == 'POST':
        # This endpoint shouldn't be used anymore since we're using Product model
        messages.error(request, "Please create products with auction option enabled instead.")
        return redirect('main:create_product')
    return redirect('main:create_product')

@login_required
def bid(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_auction=True)
    
    if product.auction_end_time and timezone.now() >= product.auction_end_time:
        messages.error(request, "This auction has ended.")
        return redirect('auction:auction_detail', product_id=product_id)
        
    amount = request.POST.get('amount')
    if amount:
        amount = Decimal(amount)
        last_bid = product.bids.order_by('-amount').first()
        increment = product.auction_increment if product.auction_increment is not None else Decimal('1')
        min_bid = (last_bid.amount if last_bid else product.price) + increment
        
        if amount >= min_bid:
            Bid.objects.create(
                product=product,
                user=request.user,
                amount=amount
            )
            messages.success(request, f"Your bid of Rp {amount:,.0f} has been placed!")
        else:
            messages.error(request, f"Minimum bid is Rp {min_bid:,.0f}")
            
    return redirect('auction:auction_detail', product_id=product_id)