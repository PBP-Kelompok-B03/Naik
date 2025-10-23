from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from main.models import Product
from .models import Order, OrderItem


@login_required
def checkout_view(request):
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        product_id = request.POST.get("product_id")
        quantity = int(request.POST.get("quantity", 1))
        address = request.POST.get("address", "Alamat default")
        payment_method = request.POST.get("payment_method", "EWALLET")
        shipping_type = request.POST.get("shipping_type", "BIASA")
        insurance = request.POST.get("insurance") == "on"
        note = request.POST.get("note", "")

        product = get_object_or_404(Product, id=product_id)

        # === Cek stok ===
        if product.stock < quantity:
            return JsonResponse({"status": "error", "message": "Stok tidak mencukupi."}, status=400)

        # === Hitung total dasar ===
        total_price = Decimal(product.price) * quantity

        # === Tambah biaya pengiriman ===
        if shipping_type == "CEPAT":
            total_price += Decimal("10000.00")
        elif shipping_type in ["SAMEDAY", "SAME_DAY"]:
            total_price += Decimal("20000.00")

        # === Tambah biaya asuransi ===
        if insurance:
            total_price += Decimal("5000.00")

        # === Buat order dengan semua data lengkap ===
        order = Order.objects.create(
            user=request.user,
            total_price=total_price,
            address=address,
            payment_method=payment_method,
            shipping_type=shipping_type,
            insurance=insurance,
            note=note,
            status="PAID",
        )

        # === Simpan item ===
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            price=product.price,
        )

        # Kurangi stok
        product.stock -= quantity
        product.count_sold += quantity
        product.save()

        return JsonResponse({
            "status": "success",
            "message": f"Order #{order.id} berhasil dibuat! Total: Rp{total_price:,.0f}",
            "order_id": order.id,
            "total": str(order.total_price),
            "product_name": product.title,
        })

    # === Handle GET ===
    product_id = request.GET.get("product_id")
    quantity = int(request.GET.get("quantity", 1))
    product = get_object_or_404(Product, id=product_id)
    total_price = Decimal(product.price) * quantity

    return render(request, "checkout/checkout.html", {
        "product": product,
        "quantity": quantity,
        "total_price": total_price,
    })

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

@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, "checkout/order_list.html", {"orders": orders})