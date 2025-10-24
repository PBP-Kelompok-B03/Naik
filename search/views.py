from django.shortcuts import render
from django.http import JsonResponse
from main.models import Product

def search_products(request):
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')

    products = Product.objects.all()

    if query:
        products = products.filter(title__icontains=query)
    if category:
        products = products.filter(category__iexact=category)
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    context = {
        'products': products,
        'query': query,
        'category': category,
        'min_price': min_price,
        'max_price': max_price,
    }

    # If AJAX, return only the partial HTML for results
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'search/search_results.html', context)

    return render(request, 'search/search_results.html', context)
