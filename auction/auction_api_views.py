from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Max
from decimal import Decimal, InvalidOperation
from main.models import Product
from .models import Bid
import json


@login_required
def auction_list_api(request):
    """API endpoint to get list of all auctions in JSON format"""
    auctions = Product.objects.filter(is_auction=True).order_by('-auction_end_time')

    auctions_data = []
    for auction in auctions:
        # Get current highest bid for each auction
        highest_bid = auction.bids.aggregate(Max('amount'))['amount__max']
        current_bid = float(highest_bid) if highest_bid else float(auction.price)

        # Check if auction is still active
        is_active = auction.auction_end_time > timezone.now() if auction.auction_end_time else False

        # Build thumbnail URL
        thumbnail_url = None
        if auction.thumbnail:
            thumbnail_url = request.build_absolute_uri(auction.thumbnail.url)

        auctions_data.append({
            'id': str(auction.id),
            'title': auction.title,
            'price': float(auction.price),
            'current_bid': current_bid,
            'category': auction.category,
            'thumbnail': thumbnail_url,
            'auction_end_time': auction.auction_end_time.isoformat() if auction.auction_end_time else None,
            'auction_increment': float(auction.auction_increment) if auction.auction_increment else None,
            'is_active': is_active,
            'seller_username': auction.user.username if auction.user else None,
        })

    return JsonResponse({'auctions': auctions_data})


@login_required
def auction_detail_api(request, product_id):
    """API endpoint to get auction detail in JSON format"""
    product = get_object_or_404(Product, id=product_id, is_auction=True)
    bids = Bid.objects.filter(product=product).order_by('-amount')
    now = timezone.now()

    # Initialize variables with default values
    current_highest = Decimal('0')
    min_bid = Decimal('0')
    highest_bid = None
    is_winner = False
    auction_active = False

    try:
        # Get highest bid and calculate values
        highest_bid = bids.first()
        current_highest = Decimal(str(highest_bid.amount)) if highest_bid else Decimal(str(product.price))

        # Calculate minimum bid
        increment = Decimal(str(product.auction_increment)) if product.auction_increment is not None else Decimal('1')
        min_bid = current_highest + increment

        # Check if auction is active
        auction_active = product.auction_end_time > now if product.auction_end_time else False

        # Determine winner after auction ends
        if not auction_active:
            winner_user = product.auction_winner or (highest_bid.user if highest_bid else None)
            if winner_user and request.user.is_authenticated and winner_user == request.user:
                is_winner = True

    except (InvalidOperation, AttributeError, ValueError):
        current_highest = Decimal('0')
        min_bid = Decimal(str(product.price))

    # Build thumbnail URL
    thumbnail_url = None
    if product.thumbnail:
        thumbnail_url = request.build_absolute_uri(product.thumbnail.url)

    # Prepare product data
    product_data = {
        'id': str(product.id),
        'title': product.title,
        'price': float(product.price),
        'current_bid': float(current_highest),
        'category': product.category,
        'thumbnail': thumbnail_url,
        'auction_end_time': product.auction_end_time.isoformat() if product.auction_end_time else None,
        'auction_increment': float(product.auction_increment) if product.auction_increment else None,
        'is_active': auction_active,
        'seller_username': product.user.username if product.user else None,
    }

    # Prepare bids data
    bids_data = []
    for bid in bids:
        bids_data.append({
            'id': str(bid.id),
            'user_username': bid.user.username,
            'amount': float(bid.amount),
            'created_at': bid.created_at.isoformat(),
        })

    response_data = {
        'product': product_data,
        'bids': bids_data,
        'current_highest_bid': float(current_highest),
        'min_bid': float(min_bid),
        'auction_active': auction_active,
        'is_winner': is_winner,
    }

    return JsonResponse(response_data)


@csrf_exempt
@login_required
def place_bid_api(request, product_id):
    """API endpoint to place a bid"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST method is allowed'}, status=405)

    product = get_object_or_404(Product, id=product_id, is_auction=True)

    # Check if auction has ended
    if product.auction_end_time and timezone.now() >= product.auction_end_time:
        return JsonResponse({
            'status': 'error',
            'message': 'This auction has ended.'
        }, status=400)

    try:
        # Parse request body
        data = json.loads(request.body)
        amount = data.get('amount')

        if not amount:
            return JsonResponse({
                'status': 'error',
                'message': 'Bid amount is required.'
            }, status=400)

        amount = Decimal(str(amount))

        # Get last bid and calculate minimum bid
        last_bid = product.bids.order_by('-amount').first()
        increment = product.auction_increment if product.auction_increment is not None else Decimal('1')
        min_bid = (last_bid.amount if last_bid else product.price) + increment

        if amount >= min_bid:
            # Create new bid
            new_bid = Bid.objects.create(
                product=product,
                user=request.user,
                amount=amount
            )

            return JsonResponse({
                'status': 'success',
                'message': f'Your bid of Rp {amount:,.0f} has been placed!',
                'bid': {
                    'id': str(new_bid.id),
                    'user_username': new_bid.user.username,
                    'amount': float(new_bid.amount),
                    'created_at': new_bid.created_at.isoformat(),
                }
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': f'Minimum bid is Rp {min_bid:,.0f}'
            }, status=400)

    except (ValueError, InvalidOperation, json.JSONDecodeError) as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Invalid bid amount: {str(e)}'
        }, status=400)
