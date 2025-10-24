from django.forms import ModelForm
from main.models import Product
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile

class ProductForm(ModelForm):
    class Meta:
        model = Product
        fields = ["title", "price", "category", "thumbnail", "stock"]
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
