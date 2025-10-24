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
        product = get_object_or_404(Product, id=product_id)

        # Check if product is in stock
        if product.stock < quantity:
            return JsonResponse({"status": "error", "message": "Stock not available"}, status=400)

        # Determine unit price based on product type
        if product.is_auction:
            # For auction: use highest bid
            highest_bid = product.bids.order_by('-amount').first()
            if highest_bid:
                unit_price = highest_bid.amount
            else:
                unit_price = product.price  # fallback to base price if no bids
        else:
            # For regular products: use seller's price
            unit_price = product.price

        # Calculate total with shipping and insurance
        total_price = unit_price * quantity
        shipping_type = request.POST.get("shipping_type", "BIASA")
        if shipping_type == "CEPAT":
            total_price += Decimal("10000.00")
        elif shipping_type in ["SAMEDAY", "SAME_DAY"]:
            total_price += Decimal("20000.00")
        
        if request.POST.get("insurance") == "on":
            total_price += Decimal("5000.00")

        # Create order
        order = Order.objects.create(
            user=request.user,
            total_price=total_price,
            address=request.POST.get("address", ""),
            payment_method=request.POST.get("payment_method", "EWALLET"),
            shipping_type=shipping_type,
            insurance=request.POST.get("insurance") == "on",
            note=request.POST.get("note", ""),
            status="PAID"
        )

        # Create order item with correct unit price
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            price=unit_price  # Save the correct unit price
        )

        # Update product stock
        product.stock -= quantity
        product.count_sold += quantity
        product.save()

        return JsonResponse({
            "status": "success",
            "message": f"Order #{order.id} created successfully! Total: Rp{total_price:,.0f}",
            "order_id": order.id,
            "total": str(total_price),
            "product_name": product.title,
        })

    # Handle GET request
    product_id = request.GET.get("product_id")
    quantity = int(request.GET.get("quantity", 1))
    product = get_object_or_404(Product, id=product_id)

    # Determine display price based on product type
    if product.is_auction:
        highest_bid = product.bids.order_by('-amount').first()
        unit_price = highest_bid.amount if highest_bid else product.price
    else:
        unit_price = product.price

    total_price = unit_price * quantity

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