from django.forms import ModelForm
from main.models import Product
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile

class ProductForm(ModelForm):
    # Add auction_duration as a non-model field
    auction_duration = forms.IntegerField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'w-full border border-gray-300 rounded-md p-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Enter duration in hours'
        })
    )

    class Meta:
        model = Product
        fields = ["title", "price", "category", "thumbnail", "stock", "is_auction", "auction_increment"]
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
            "is_auction": forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
            "auction_increment": forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-md p-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Enter increment amount'
            }),
        }

    # Override default thumbnail field to accept .avif
    thumbnail = forms.ImageField(
        required=True,
        widget=forms.ClearableFileInput(attrs={
            'accept': '.avif',
            'class': 'w-full border border-gray-300 rounded-md p-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )


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
