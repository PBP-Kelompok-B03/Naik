from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Max
from decimal import Decimal, InvalidOperation
from main.models import Product
from .models import Bid
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json

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
            messages.error(request, f"Minimum bid is Rp {min_bid:,.0f}")
            
    return redirect('auction:auction_detail', product_id=product_id)

def api_auction_list(request):
    """
    API endpoint to get list of auctions.
    Returns JSON with list of auction products.
    """
    auctions = Product.objects.filter(is_auction=True).order_by('-auction_end_time')
    data = []
    
    for auction in auctions:
        # Get current highest bid
        highest_bid = auction.bids.aggregate(Max('amount'))['amount__max']
        current_bid = highest_bid if highest_bid else auction.price
        
        # Check if auction is active
        is_active = auction.auction_end_time > timezone.now() if auction.auction_end_time else False
        
        data.append({
            'id': str(auction.id),
            'title': auction.title,
            'price': float(auction.price),
            'current_bid': float(current_bid),
            'category': auction.category,
            'thumbnail': auction.thumbnail.url if auction.thumbnail else None,
            'auction_end_time': auction.auction_end_time.isoformat() if auction.auction_end_time else None,
            'auction_increment': float(auction.auction_increment) if auction.auction_increment else None,
            'is_active': is_active,
            'seller_username': auction.user.username if auction.user else None,
        })
    
    return JsonResponse({'auctions': data})

def api_auction_detail(request, product_id):
    """
    API endpoint to get auction detail.
    Returns JSON with auction details and bids.
    """
    product = get_object_or_404(Product, id=product_id, is_auction=True)
    bids = Bid.objects.filter(product=product).order_by('-amount')
    now = timezone.now()
    
    # Get highest bid and calculate values
    highest_bid = bids.first()
    current_highest = float(highest_bid.amount) if highest_bid else float(product.price)
    
    # Min bid
    increment = float(product.auction_increment) if product.auction_increment else 1.0
    min_bid = current_highest + increment
    
    # Check if auction is active
    auction_active = product.auction_end_time > now if product.auction_end_time else False
    
    # Determine winner
    is_winner = False
    if not auction_active:
        winner_user = product.auction_winner or (highest_bid.user if highest_bid else None)
        # TEMPORARILY USE FIRST ACTIVE USER FOR TESTING
        from django.contrib.auth.models import User
        try:
            test_user = User.objects.filter(is_active=True).first()
            if winner_user and test_user and winner_user == test_user:
                is_winner = True
        except:
            pass
    
    # Bids data
    bids_data = []
    for bid in bids:
        bids_data.append({
            'id': str(bid.id),
            'user_username': bid.user.username,
            'amount': float(bid.amount),
            'created_at': bid.created_at.isoformat(),
        })
    
    data = {
        'product': {
            'id': str(product.id),
            'title': product.title,
            'price': float(product.price),
            'category': product.category,
            'thumbnail': product.thumbnail.url if product.thumbnail else None,
            'auction_end_time': product.auction_end_time.isoformat() if product.auction_end_time else None,
            'auction_increment': float(product.auction_increment) if product.auction_increment else None,
            'seller_username': product.user.username if product.user else None,
        },
        'bids': bids_data,
        'current_highest_bid': current_highest,
        'min_bid': min_bid,
        'auction_active': auction_active,
        'is_winner': is_winner,
    }
    
    return JsonResponse(data)

@csrf_exempt
# @login_required  # Temporarily disabled for testing
@require_POST
def api_place_bid(request, product_id):
    """
    API endpoint to place a bid on an auction.
    Accepts POST with 'amount' field.
    Returns JSON response.
    """
    product = get_object_or_404(Product, id=product_id, is_auction=True)
    
    if product.auction_end_time and timezone.now() >= product.auction_end_time:
        return JsonResponse({'error': 'This auction has ended.'}, status=400)
    
    # TEMPORARILY USE FIRST ACTIVE USER FOR TESTING
    from django.contrib.auth.models import User
    try:
        user = User.objects.filter(is_active=True).first()
        if not user:
            return JsonResponse({'error': 'No active users found.'}, status=500)
    except Exception as e:
        return JsonResponse({'error': f'Database error: {str(e)}'}, status=500)
    
    # Try to get amount from POST data or JSON body
    amount_str = request.POST.get('amount')
    if not amount_str:
        try:
            body = json.loads(request.body.decode() or "{}")
            amount_str = body.get('amount')
        except Exception:
            pass
    
    if not amount_str:
        return JsonResponse({'error': 'Amount is required.'}, status=400)
    
    try:
        amount = Decimal(amount_str)
    except (InvalidOperation, ValueError):
        return JsonResponse({'error': 'Invalid amount format.'}, status=400)
    
    # Calculate minimum bid
    last_bid = product.bids.order_by('-amount').first()
    increment = product.auction_increment if product.auction_increment is not None else Decimal('1')
    min_bid = (last_bid.amount if last_bid else product.price) + increment
    
    if amount < min_bid:
        return JsonResponse({
            'error': f'Minimum bid is Rp {min_bid:,.0f}',
            'min_bid': float(min_bid)
        }, status=400)
    
    # Create the bid
    bid = Bid.objects.create(
        product=product,
        user=user,
        amount=amount
    )
    
    return JsonResponse({
        'success': True,
        'bid_id': str(bid.id),
        'amount': float(amount),
        'message': f'Your bid of Rp {amount:,.0f} has been placed!'
    })