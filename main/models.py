import uuid
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.forms import ModelForm
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone

class Product(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    CATEGORY_CHOICES = [
        ("Men's Shoes", "Men's Shoes"),
        ("Women's Shoes", "Women's Shoes"),
        ("Kids' Shoes", "Kids' Shoes"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default="Men's Shoes")
    thumbnail = models.ImageField(upload_to='image/products/temp/', null=True, blank=True)
    count_sold = models.PositiveIntegerField(default=0)
    stock = models.PositiveIntegerField(default=10)
    is_auction = models.BooleanField(default=False)
    auction_increment = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
    auction_end_time = models.DateTimeField(null=True, blank=True)
    auction_winner = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='auction_wins'
    )

    def __str__(self):
        return self.title

    def is_in_stock(self):
        return self.stock > 0

    def get_highest_bid(self):
        """Get the highest bid amount for this auction product"""
        if not self.is_auction:
            return None
        highest_bid = self.bids.aggregate(models.Max('amount'))['amount__max']
        return highest_bid if highest_bid else self.price

    def get_auction_winner(self):
        """Get the winner of the auction (user with highest bid)"""
        if not self.is_auction or self.auction_end_time > timezone.now():
            return None
        
        # Get the bid with highest amount
        highest_bid = self.bids.order_by('-amount', '-created_at').first()
        return highest_bid.user if highest_bid else None

    def is_auction_ended(self):
        """Check if auction has ended"""
        return self.is_auction and self.auction_end_time <= timezone.now()

    def can_user_checkout(self, user):
        """Check if user can checkout this auction product"""
        if not self.is_auction:
            return True  # Regular products can be checked out by anyone
        
        if not self.is_auction_ended():
            return False  # Auction still active
        
        winner = self.get_auction_winner()
        return winner == user if winner else False


class Profile(models.Model):
    ROLE_CHOICES = [
        ('buyer', 'Buyer'),
        ('seller', 'Seller'),
        ('admin', 'Admin'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='buyer')

    def __str__(self):
        return f"{self.user.username} - {self.role}"


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance, role='buyer')
    else:
        instance.profile.save()

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
