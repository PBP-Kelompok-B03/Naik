import traceback
from django.shortcuts import render
from django.forms import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponseBadRequest
from django.urls import reverse
from django.contrib import messages

from .forms import CommentForm
from .models import Comment, Reply
from checkout.models import OrderItem

@login_required
def create_comment(request):
    """
    POST handler untuk membuat komentar baru.
    Jika comment milik user untuk order_item sudah ada -> update comment tersebut.
    """
    if request.method != 'POST':
        return HttpResponseBadRequest("Only POST allowed")

    form = CommentForm(request.POST)
    order_item_id = request.POST.get('order_item_id')
    if not order_item_id:
        return HttpResponseBadRequest("Missing order_item_id")

    order_item = get_object_or_404(OrderItem, pk=order_item_id)

    # validate owner
    if getattr(order_item.order, 'user', None) != request.user:
        return HttpResponseForbidden("You cannot comment on items that are not yours.")

    # check status
    allowed_statuses = ['DELIVERED', 'COMPLETED', 'PAID']  # sesuaikan
    order_status = getattr(order_item.order, 'status', '').upper()
    if order_status not in allowed_statuses:
        messages.error(request, "You can add reviews only for completed/delivered orders.")
        return redirect(request.META.get('HTTP_REFERER', reverse('checkout:order_list')))

    # check existing comment by this user for this order_item
    existing = Comment.objects.filter(order_item=order_item, author=request.user).first()

    if not form.is_valid():
        messages.error(request, "Formulir komentar tidak valid.")
        return redirect(request.META.get('HTTP_REFERER', reverse('checkout:order_list')))

    # ambil data dari form
    content = form.cleaned_data.get('content')
    rating = form.cleaned_data.get('rating') if 'rating' in form.cleaned_data else None

    if existing:
        # update existing comment
        existing.content = content
        existing.rating = rating
        try:
            existing.save()
            messages.success(request, "Komentar berhasil diperbarui.")
        except Exception as e:
            traceback.print_exc()
            messages.error(request, f"Gagal memperbarui komentar: {e}")
    else:
        # create new comment
        product = order_item.product
        comment = form.save(commit=False)
        comment.order_item = order_item
        comment.product = product
        comment.author = request.user
        try:
            comment.save()
            messages.success(request, "Komentar/ulasan berhasil ditambahkan.")
        except Exception as e:
            traceback.print_exc()
            messages.error(request, f"Gagal menyimpan komentar: {e}")

    return redirect(request.META.get('HTTP_REFERER', reverse('checkout:order_list')))

@login_required
def edit_comment(request, comment_id):
    """
    Edit/update existing comment.
    - GET: (opsional) render form untuk edit (comments/edit_comment.html)
    - POST: update content and rating, redirect back (to referer or order_list)
    """
    comment = get_object_or_404(Comment, pk=comment_id)

    # hanya author yang boleh edit
    if comment.author != request.user:
        return HttpResponseForbidden("Hanya penulis komentar yang dapat mengedit komentar ini.")

    if request.method == 'POST':
        content = (request.POST.get('content') or '').strip()
        rating_raw = request.POST.get('rating', '').strip()

        # Validasi konten
        if not content:
            messages.error(request, "Isi komentar tidak boleh kosong.")
            return redirect(request.META.get('HTTP_REFERER', reverse('checkout:order_list')))

        # Validasi rating (boleh kosong -> set None)
        if rating_raw == '':
            rating = None
        else:
            try:
                rating = int(rating_raw)
                if rating < 1 or rating > 5:
                    raise ValueError
            except ValueError:
                messages.error(request, "Rating harus berupa angka antara 1 dan 5.")
                return redirect(request.META.get('HTTP_REFERER', reverse('checkout:order_list')))

        # Terapkan perubahan
        comment.content = content
        comment.rating = rating

        try:
            comment.save()  # akan memanggil full_clean jika model mengimplementasikannya
            messages.success(request, "Komentar berhasil diperbarui.")
        except ValidationError as e:
            messages.error(request, "Gagal menyimpan komentar: " + "; ".join(e.messages))
        except Exception as e:
            messages.error(request, f"Gagal memperbarui komentar: {e}")

        return redirect(request.META.get('HTTP_REFERER', reverse('checkout:order_list')))

    # Jika GET: render halaman edit sederhana (opsional)
    return render(request, "comments/edit_comment.html", {"comment": comment})

@login_required
def reply_to_comment(request, comment_id):
    """
    Penjual membalas komentar. Pastikan request.user adalah penjual dari product tersebut.
    Expect POST with 'content'.
    """
    if request.method != 'POST':
        return HttpResponseBadRequest("Only POST allowed")

    comment = get_object_or_404(Comment, pk=comment_id)
    product = comment.product

    # Adaptasi: cari cara menentukan penjual product.
    # Contoh asumsi: Product punya field `seller` yang merujuk ke user
    seller = getattr(product, 'seller', None) or getattr(product, 'owner', None)
    if seller is None:
        return HttpResponseBadRequest("Product seller is not defined; cannot verify permission.")

    if getattr(seller, 'pk') != request.user.pk:
        return HttpResponseForbidden("Hanya penjual produk ini yang dapat membalas komentar.")

    content = request.POST.get('content', '').strip()
    if not content:
        messages.error(request, "Isi balasan tidak boleh kosong.")
        return redirect(request.META.get('HTTP_REFERER', reverse('main:product_detail', args=[product.pk])))

    reply = Reply(comment=comment, author=request.user, content=content)
    try:
        reply.save()
        messages.success(request, "Balasan berhasil disimpan.")
    except Exception as e:
        messages.error(request, f"Gagal menyimpan balasan: {e}")

    return redirect(request.META.get('HTTP_REFERER', reverse('main:product_detail', args=[product.pk])))
