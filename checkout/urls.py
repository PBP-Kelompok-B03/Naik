from django.urls import path
from . import views

app_name = 'checkout'

urlpatterns = [
    path('', views.checkout_view, name='checkout_view'),
    path('success/', views.checkout_success, name='checkout_success'),
]
