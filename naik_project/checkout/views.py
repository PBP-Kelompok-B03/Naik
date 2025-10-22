from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from .models import Order, OrderItem, Product


@login_required
def checkout_view(request):
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        # Ambil data dari form
        product_id = request.POST.get("product_id")
        address = request.POST.get("address", "")
        payment_method = request.POST.get("payment_method", "EWALLET")

        # Ambil produk berdasarkan ID
        product = get_object_or_404(Product, id=product_id)
        total_price = Decimal(product.price)

        # Buat order baru
        order = Order.objects.create(
            user=request.user,
            total_price=total_price,
            address=address,
            payment_method=payment_method,
        )

        # Buat item order
        OrderItem.objects.create(
            order=order,
            product_name=product.name,
            quantity=1,
            price=total_price,
        )

        return JsonResponse({
            "status": "success",
            "message": f"Order #{order.id} berhasil dibuat!",
            "order_id": order.id,
            "total": str(order.total_price),
            "product_name": product.name,
        })

    return render(request, "checkout/checkout.html")


@login_required
def checkout_success(request):
    # Ambil order terakhir user untuk ditampilkan
    order = Order.objects.filter(user=request.user).last()
    return render(request, "checkout/success.html", {
        "name": request.user.username,
        "order": order,
        "product_name": order.items.first().product_name if order and order.items.exists() else "-",
    })
