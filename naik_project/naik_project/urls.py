from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('checkout/', include('checkout.urls')),
    path('comments/', include('comments.urls')),
    path('main/', include('main.urls')),
    path('auction/', include('auction.urls')),
]
