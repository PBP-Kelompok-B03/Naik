from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from main.models import Product
from .models import Order, OrderItem


@login_required
def checkout_view(request):
    # === HANDLE POST (AJAX) ===
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        product_id = request.POST.get("product_id")
        quantity = int(request.POST.get("quantity", 1))
        address = request.POST.get("address", "Alamat default")
        payment_method = request.POST.get("payment_method", "EWALLET")

        product = get_object_or_404(Product, id=product_id)

        # Cek stok
        if product.stock < quantity:
            return JsonResponse({"status": "error", "message": "Stok tidak mencukupi."}, status=400)

        total_price = Decimal(product.price) * quantity

        # Buat order
        order = Order.objects.create(
            user=request.user,
            total_price=total_price,
            address=address,
            payment_method=payment_method,
        )

        # Tambah item order
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            price=product.price,
        )

        # Kurangi stok & update jumlah terjual
        product.stock -= quantity
        product.count_sold += quantity
        product.save()

        return JsonResponse({
            "status": "success",
            "message": f"Order #{order.id} berhasil dibuat! Total: Rp{total_price:,}",
            "order_id": order.id,
            "total": str(order.total_price),
            "product_name": product.title,
        })

    # === HANDLE GET (TAMPILKAN HALAMAN CHECKOUT) ===
    product_id = request.GET.get("product_id")
    quantity = int(request.GET.get("quantity", 1))

    product = get_object_or_404(Product, id=product_id)
    total_price = Decimal(product.price) * quantity

    context = {
        "product": product,
        "quantity": quantity,
        "total_price": total_price,
    }

    return render(request, "checkout/checkout.html", context)


@login_required
def checkout_success(request):
    order = Order.objects.filter(user=request.user).last()
    if not order:
        return redirect('main:show_main')
    item = order.items.first()
    return render(request, "checkout/success.html", {
        "name": request.user.username,
        "order": order,
        "product_name": item.product.title if item else "-",
    })
