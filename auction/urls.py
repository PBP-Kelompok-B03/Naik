from django.urls import path
from .views import auction_list, create_auction, auction_detail, bid, api_auction_list, api_auction_detail, api_place_bid

app_name = 'auction'

urlpatterns = [
    path('', auction_list, name='auction_list'),
    path('create/', create_auction, name='create_auction'),
    # Remove spaces after auction/
    path('product/<uuid:product_id>/', auction_detail, name='auction_detail'),
    path('bid/<uuid:product_id>/', bid, name='place_bid'),
    
    # API endpoints
    path('api/list/', api_auction_list, name='api_auction_list'),
    path('api/product/<uuid:product_id>/', api_auction_detail, name='api_auction_detail'),
    path('api/bid/<uuid:product_id>/', api_place_bid, name='api_place_bid'),
]