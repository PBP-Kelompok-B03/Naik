from django.forms import ModelForm
from main.models import Product
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile

class ProductForm(ModelForm):
    is_auction = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'mr-2'
        })
    )
    auction_increment = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full border border-gray-300 rounded-md p-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
            'min': 1,
            'placeholder': 'Auction increment (in Rupiah)',
        })
    )
    auction_duration = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full border border-gray-300 rounded-md p-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
            'min': 1,
            'placeholder': 'Auction duration (in hours)',
        })
    )

    class Meta:
        model = Product
        fields = ["title", "price", "category", "thumbnail", "stock", "is_auction", "auction_increment", "auction_duration"]
        widgets = {
            "title": forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-md p-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            "price": forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-md p-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            "category": forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-md p-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            "stock": forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-md p-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'min': 0,
                'placeholder': 'Enter stock amount',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make auction fields required when is_auction is checked
        if self.data and self.data.get('is_auction') == 'on':
            self.fields['auction_increment'].required = True
            self.fields['auction_duration'].required = True

    def clean(self):
        cleaned_data = super().clean()
        is_auction = cleaned_data.get('is_auction')
        
        if is_auction:
            auction_increment = cleaned_data.get('auction_increment')
            auction_duration = cleaned_data.get('auction_duration')
            
            if not auction_increment:
                raise forms.ValidationError("Auction increment is required for auction products.")
            if not auction_duration:
                raise forms.ValidationError("Auction duration is required for auction products.")
            
            if auction_increment and auction_increment <= 0:
                raise forms.ValidationError("Auction increment must be greater than 0.")
            if auction_duration and auction_duration <= 0:
                raise forms.ValidationError("Auction duration must be greater than 0.")
        
        return cleaned_data


class CustomUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=Profile.ROLE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full border border-gray-300 rounded-md p-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role']
