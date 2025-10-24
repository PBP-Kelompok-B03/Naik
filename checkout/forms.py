from django import forms
from .models import Order, OrderItem

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['address', 'payment_method']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Masukkan alamat lengkap'}),
            'payment_method': forms.Select(),
        }
