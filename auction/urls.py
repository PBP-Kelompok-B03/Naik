from django.urls import path
from .views import auction_list, create_auction, auction_detail, bid
from .auction_api_views import auction_list_api, auction_detail_api, place_bid_api

app_name = 'auction'

urlpatterns = [
    # HTML views
    path('', auction_list, name='auction_list'),
    path('create/', create_auction, name='create_auction'),
    # Remove spaces after auction/
    path('product/<uuid:product_id>/', auction_detail, name='auction_detail'),
    path('bid/<uuid:product_id>/', bid, name='place_bid'),

    # API endpoints for mobile app
    path('api/list/', auction_list_api, name='auction_list_api'),
    path('api/product/<uuid:product_id>/', auction_detail_api, name='auction_detail_api'),
    path('api/bid/<uuid:product_id>/', place_bid_api, name='place_bid_api'),
]