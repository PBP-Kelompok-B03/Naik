from django.contrib import admin
from .models import Auction, Bid

@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = ('title', 'seller', 'status', 'duration')
    search_fields = ('title',)
    list_filter = ('status',)

@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'amount', 'created_at')
    search_fields = ('product__title', 'user__username')
    list_filter = ('product', 'user')