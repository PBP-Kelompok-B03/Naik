from django.urls import path
from .views import auction_list, create_auction, auction_detail, bid

app_name = 'auction'

urlpatterns = [
    path('', auction_list, name='auction_list'),
    path('create/', create_auction, name='create_auction'),
    # Remove spaces after auction/
    path('product/<uuid:product_id>/', auction_detail, name='auction_detail'),
    path('bid/<uuid:product_id>/', bid, name='place_bid'),
]