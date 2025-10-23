import uuid
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

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
    thumbnail = models.CharField(max_length=255, blank=True, null=True)
    count_sold = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title
    
    
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