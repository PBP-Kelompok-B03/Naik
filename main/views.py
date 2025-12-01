from django.shortcuts import render, redirect, get_object_or_404
from main.forms import ProductForm
from main.models import Product
from django.http import HttpResponse
from django.core import serializers
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
import datetime
from django.http import HttpResponseRedirect
from django.urls import reverse
from .forms import CustomUserCreationForm
from .models import Profile
import os
from django.conf import settings
from django.http import HttpResponseForbidden
from main.forms import ProductForm
from main.models import Product
from django.db.models import Max  # Tambahkan import ini
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

import csv, os
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from main.models import Product
import requests

from django.views.decorators.csrf import csrf_exempt
from django.utils.html import strip_tags
import json
from django.http import JsonResponse


# @login_required(login_url='/login')
def show_main(request):
    filter_type = request.GET.get("filter", "all")  # default 'all'

    if filter_type == "all":
        product_list = Product.objects.all()
    else:
        product_list = Product.objects.filter(user=request.user)

    context = {
        'name': request.user.username,
        'product_list': product_list,
        'last_login': request.COOKIES.get('last_login', 'Never')
    }
    return render(request, "main.html",context)

@login_required(login_url='/login')
def create_product(request):
    # Only 'seller' and 'admin' can add products
    if request.user.profile.role not in ['seller', 'admin']:
        return HttpResponseForbidden("You don't have permission to add products.")

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.user = request.user

            # Handle auction settings
            if form.cleaned_data.get('is_auction'):
                product.is_auction = True
                product.auction_increment = form.cleaned_data.get('auction_increment')
                duration_hours = form.cleaned_data.get('auction_duration', 24)
                product.auction_end_time = timezone.now() + timedelta(hours=duration_hours)

            product.save()
            return redirect('main:show_main')
    else:
        form = ProductForm()

    return render(request, "create_product.html", {'form': form})

@login_required(login_url='/login')
def show_product(request, id):
    product = get_object_or_404(Product, pk=id)
    context = {
        'product': product,
        'current_time': timezone.now(),
    }
    
    if product.is_auction:
        # Get current highest bid
        highest_bid = product.bids.aggregate(Max('amount'))['amount__max']
        context['current_highest_bid'] = highest_bid if highest_bid else product.price
        
        # Calculate minimum bid
        last_bid = product.bids.order_by('-amount').first()
        min_bid = (last_bid.amount if last_bid else product.price) + product.auction_increment
        context['min_bid'] = min_bid
        
        # Check if auction is still active
        context['auction_active'] = product.auction_end_time > timezone.now()
        
    return render(request, "product_detail.html", context)

def show_xml(request):
     product_list = Product.objects.all()
     xml_data = serializers.serialize("xml", product_list)
     return HttpResponse(xml_data, content_type="application/xml")

def show_json(request):
    product_list = Product.objects.all()
    json_data = serializers.serialize("json", product_list)
    return HttpResponse(json_data, content_type="application/json")

def show_xml_by_id(request, product_id):
   try:
       product_item = Product.objects.filter(pk=product_id)
       xml_data = serializers.serialize("xml", product_item)
       return HttpResponse(xml_data, content_type="application/xml")
   except Product.DoesNotExist:
       return HttpResponse(status=404)
   
def show_json_by_id(request, product_id):
   try:
       product_item = Product.objects.get(pk=product_id)
       json_data = serializers.serialize("json", [product_item])
       return HttpResponse(json_data, content_type="application/json")
   except Product.DoesNotExist:
       return HttpResponse(status=404)

def register(request):
    form = CustomUserCreationForm()

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            role = form.cleaned_data.get('role')
            profile, created = Profile.objects.get_or_create(user=user)
            profile.role = role
            profile.save()
            messages.success(request, 'Your account has been successfully created!')
            return redirect('main:login')
        else:
            print(form.errors)  

    context = {'form': form}
    return render(request, 'register.html', context)

def login_user(request):
   if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            response = HttpResponseRedirect(reverse("main:show_main"))
            response.set_cookie('last_login', str(datetime.datetime.now()))
            return response

   else:
      form = AuthenticationForm(request)
   context = {'form': form}
   return render(request, 'login.html', context)

def logout_user(request):
    logout(request)
    response = HttpResponseRedirect(reverse('main:login'))
    response.delete_cookie('last_login')
    return response

def edit_product(request, id):
    product = get_object_or_404(Product, pk=id)
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if form.is_valid() and request.method == 'POST':
        form.save()
        return redirect('main:show_main')

    context = {
        'form': form
    }

    return render(request, "edit_product.html", context)

@login_required(login_url='/login')
def delete_product(request, id):
    product = Product.objects.get(id=id)

    # Buyers can never delete
    if request.user.profile.role == 'buyer':
        return HttpResponseForbidden("Buyers cannot delete products.")

    # Sellers can only delete their own
    if request.user.profile.role == 'seller' and product.user != request.user:
        return HttpResponseForbidden("You can only delete your own products.")

    # Admins can delete anything, no restrictions
    product.delete()
    messages.success(request, f"Product '{product.title}' has been deleted successfully!")
    return redirect('main:show_main')

@user_passes_test(lambda u: u.is_superuser or u.profile.role == 'admin')
def load_dataset(request):
    csv_path = os.path.join(settings.BASE_DIR, 'static', 'data', 'products.csv')
    image_dir = 'image/products'  # relative path inside static/

    if not os.path.exists(csv_path):
        return JsonResponse({'error': 'Dataset CSV not found'}, status=404)

    created_count = 0
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for idx, row in enumerate(reader, start=1):
            product_name = row.get('Product Name')
            price = row.get('Price (IDR)')
            category = row.get('Category')

            if not product_name or not price:
                continue  # skip invalid rows

            # Clean price (e.g. "2.379.000" → 2379000)
            price_clean = int(str(price).replace('.', '').replace(',', '').strip())

            Product.objects.get_or_create(
                title=product_name.strip(),
                price=price_clean,
                category=category.strip(),
                defaults={
                    'user': request.user,
                    'thumbnail': f'{image_dir}/{idx}.avif',
                    'stock': 10,
                }
            )
            created_count += 1

    return JsonResponse({'message': f'{created_count} products loaded successfully!'})

def proxy_image(request):
    image_url = request.GET.get('url')
    if not image_url:
        return HttpResponse('No URL provided', status=400)
    
    try:
        # Fetch image from external source
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        
        # Return the image with proper content type
        return HttpResponse(
            response.content,
            content_type=response.headers.get('Content-Type', 'image/jpeg')
        )
    except requests.RequestException as e:
        return HttpResponse(f'Error fetching image: {str(e)}', status=500)
    

@csrf_exempt
def create_product_flutter(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        title = strip_tags(data.get("title", ""))  # Strip HTML tags
        content = strip_tags(data.get("content", ""))  # Strip HTML tags
        category = data.get("category", "")
        thumbnail = data.get("thumbnail", "")
        is_featured = data.get("is_featured", False)
        user = request.user
        
        new_product = Product(
            title=title, 
            content=content,
            category=category,
            thumbnail=thumbnail,
            is_featured=is_featured,
            user=user
        )
        new_product.save()
        
        return JsonResponse({"status": "success"}, status=200)
    else:
        return JsonResponse({"status": "error"}, status=401)