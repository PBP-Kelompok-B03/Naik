import uuid
from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from main.models import Product


class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    PAYMENT_CHOICES = [
        ('COD', 'Cash on Delivery'),
        ('TRANSFER', 'Transfer Bank'),
        ('EWALLET', 'E-Wallet'),
        ('CREDIT', 'Kartu Kredit'),
    ]

    SHIPPING_CHOICES = [
        ('BIASA', 'Biasa (2–4 hari)'),
        ('CEPAT', 'Cepat (1–2 hari)'),
        ('SAME_DAY', 'Same Day (hari ini)'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('SHIPPED', 'Shipped'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    address = models.TextField()
    # default should match the choice keys (e.g. 'EWALLET')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='EWALLET')
    shipping_type = models.CharField(max_length=20, choices=SHIPPING_CHOICES, default='BIASA')
    insurance = models.BooleanField(default=False)
    note = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PAID')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"


class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=12, decimal_places=2)

    def get_total_price(self):
        return self.quantity * self.price

    def __str__(self):
        return f"{self.product.title} x {self.quantity}"
