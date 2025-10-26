from django import forms
from .models import Auction, Bid

class AuctionForm(forms.ModelForm):
    class Meta:
        model = Auction
        fields = ['title']

class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['amount']