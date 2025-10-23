from django.forms import ModelForm
from main.models import Product
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile

class ProductForm(ModelForm):
    class Meta:
        model = Product
        fields = ["title", "price", "category", "thumbnail"]

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
