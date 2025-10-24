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

import csv, os
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from main.models import Product



# @login_required(login_url='/login')
def show_main(request):
    filter_type = request.GET.get("filter", "all")  # default 'all'

    if filter_type == "all":
        product_list = Product.objects.all()
    else:
        product_list = Product.objects.filter(user=request.user)

    context = {
        'npm': '240123456',
        'name': request.user.username,
        'class': 'PBP A',
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
            product.save()

            # Save image as static/image/products/<index>.avif
            uploaded_file = request.FILES.get('thumbnail')
            if uploaded_file:
                products_dir = os.path.join(settings.BASE_DIR, 'static', 'image', 'products')
                os.makedirs(products_dir, exist_ok=True)

                # Find the next available index
                existing_files = [f for f in os.listdir(products_dir) if f.endswith('.avif')]
                next_index = len(existing_files) + 1
                new_filename = f"{next_index}.avif"
                new_path = os.path.join(products_dir, new_filename)

                # Save uploaded file
                with open(new_path, 'wb+') as destination:
                    for chunk in uploaded_file.chunks():
                        destination.write(chunk)

                # Update product thumbnail path
                product.thumbnail = f"image/products/{new_filename}"
                product.save()

            return redirect('main:show_main')
    else:
        form = ProductForm()

    return render(request, "create_product.html", {'form': form})

@login_required(login_url='/login')
def show_product(request, id):
    product = get_object_or_404(Product, pk=id)

    context = {
        'product': product
    }

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
            print(form.errors)  # 👈 ADD THIS LINE to show what’s wrong in the terminal

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
    form = ProductForm(request.POST or None, instance=product)
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
    if request.user.profile.role == 'seller' and product.owner != request.user:
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