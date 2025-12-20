from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
import json

from main.models import Product
from .models import Order, OrderItem


# ======================================================
# WEB VIEWS (PAKAI login_required)
# ======================================================

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

        if product.stock < quantity:
            return JsonResponse(
                {"status": "error", "message": "Stok tidak mencukupi."},
                status=400
            )

        total_price = Decimal(product.price) * quantity

        if shipping_type == "CEPAT":
            total_price += Decimal("10000")
        elif shipping_type in ["SAMEDAY", "SAME_DAY"]:
            total_price += Decimal("20000")

        if insurance:
            total_price += Decimal("5000")

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

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            price=product.price,
        )

        product.stock -= quantity
        product.count_sold += quantity
        product.save()

        return JsonResponse({
            "status": "success",
            "order_id": str(order.id),
            "total": str(order.total_price),
        })

    product_id = request.GET.get("product_id")
    quantity = int(request.GET.get("quantity", 1))
    product = get_object_or_404(Product, id=product_id)

    return render(request, "checkout/checkout.html", {
        "product": product,
        "quantity": quantity,
        "total_price": Decimal(product.price) * quantity,
    })


@login_required
def checkout_success(request):
    order = Order.objects.filter(user=request.user).last()
    if not order:
        return redirect('main:show_main')

    item = order.items.first()
    return render(request, "checkout/success.html", {
        "order": order,
        "product_name": item.product.title if item else "-",
    })


@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "checkout/order_list.html", {"orders": orders})


# ===========================
# PLACE ORDER (FLUTTER API)
# ===========================
@csrf_exempt
def place_order(request):
    # if not request.user.is_authenticated:
    #     return JsonResponse(
    #         {"status": "error", "message": "Unauthorized"},
    #         status=401
    #     )

    if request.method != "POST":
        return JsonResponse(
            {"status": "error", "message": "POST only"},
            status=405
        )

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse(
            {"status": "error", "message": "Invalid JSON"},
            status=400
        )

    product_id = data.get("product_id")
    quantity = int(data.get("quantity", 1))
    address = data.get("address", "")
    payment_method = data.get("payment_method", "EWALLET")
    shipping_type = data.get("shipping_type", "REGULER")
    insurance = data.get("insurance", False)
    note = data.get("note", "")

    if isinstance(insurance, str):
        insurance = insurance.lower() == "true"

    product = Product.objects.get(id=product_id)

    if product.stock < quantity:
        return JsonResponse(
            {"status": "error", "message": "Stok tidak cukup"},
            status=400
        )

    total_price = Decimal(product.price) * quantity

    if shipping_type == "NEXTDAY":
        total_price += Decimal("10000")
    elif shipping_type == "SAMEDAY":
        total_price += Decimal("15000")

    if insurance:
        total_price += Decimal("5000")

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

    OrderItem.objects.create(
        order=order,
        product=product,
        quantity=quantity,
        price=product.price,
    )

    product.stock -= quantity
    product.count_sold += quantity
    product.save()

    return JsonResponse({
        "status": "success",
        "order_id": str(order.id),
        "total_price": str(order.total_price),
    })


# ===========================
# ORDER LIST (FLUTTER API)
# ===========================
def order_list_api(request):
    # if not request.user.is_authenticated:
    #     return JsonResponse(
    #         {"error": "Unauthorized"},
    #         status=401
    #     )

    orders = Order.objects.filter(user=request.user).order_by("-created_at")

    data = []
    for order in orders:
        data.append({
            "id": str(order.id),
            "total_price": str(order.total_price),
            "status": order.status,
            "created_at": order.created_at.strftime("%d %b %Y %H:%M"),
        })

    return JsonResponse(data, safe=False)