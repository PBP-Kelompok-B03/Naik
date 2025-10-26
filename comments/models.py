from django.db import models
from django.contrib.auth.models import User
from django.forms import ValidationError
from main.models import Product
from checkout.models import OrderItem

# Create your models here.
class Comment(models.Model):
    """
    Komentar / Ulasan yang dibuat oleh pembeli terhadap produk yang sudah dibelinya.
    - Setiap comment terhubung ke satu Product dan satu OrderItem (produk dalam order).
    - author disimpan untuk kemudahan query (walau bisa juga diambil dari order_item.order.user).
    - parent bisa dipakai bila ingin threading (reply as child comment). Namun aku sarankan
      memakai model Reply terpisah bila hanya penjual yang bisa membalas.
    """
    id = models.UUIDField(primary_key=True, null=False, editable=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='comments')
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    rating = models.PositiveSmallIntegerField(default=5, help_text="Optional rating: 1-5")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_visible = models.BooleanField(default=True, help_text="Jika false, komentar tidak ditampilkan")

    class Meta:
        ordering = ['-created_at']
        # optional: mencegah duplikat komentar untuk satu order_item (mis. satu pembeli hanya 1 ulasan per item)
        unique_together = ('order_item',)  # ubah sesuai kebijakan

    def __str__(self):
        prod_title = getattr(self.product, "title", str(self.product))
        author_name = getattr(self.author, "username", str(self.author))
        return f"Comment on {prod_title} by {author_name}"

    # def clean(self):
    #     # Validasi: order_item harus cocok produk dan author harus pemilik order
    #     if self.order_item.product != self.product:
    #         raise ValidationError("OrderItem.product harus sesuai dengan field product pada komentar.")
    #     order_user = getattr(self.order_item.order, "user", None)
    #     if order_user != self.author:
    #         raise ValidationError("Hanya pemilik order yang dapat mengomentari order item ini.")

    def save(self, *args, **kwargs):
        self.full_clean()  # jalankan clean() sebelum save
        super().save(*args, **kwargs)


class Reply(models.Model):
    """
    Balasan yang dibuat (biasanya) oleh Penjual terhadap Comment.
    Dipisah agar lebih jelas: hanya comments yang dapat direply, dan replies punya author sendiri (seller).
    """
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="replies")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="replies")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_visible = models.BooleanField(default=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Reply to Comment {self.comment.id} by {getattr(self.author, 'username', self.author)}"

    # def clean(self):
    #     # Opsional: pastikan author memang penjual dari produk tersebut
    #     product = self.comment.product
    #     # Asumsi: Product punya field owner/seller -> product.seller / product.owner (sesuaikan)
    #     seller_field_names = ['seller', 'owner']
    #     seller = None
    #     for f in seller_field_names:
    #         seller = getattr(product, f, None)
    #         if seller:
    #             break
    #     if seller and getattr(self.author, 'pk', None) != getattr(seller, 'pk', None):
    #         raise ValidationError("Hanya penjual produk ini yang dapat membalas komentarnya.")
    #     # Jika tidak ada field seller di Product, skip validation (atau sesuaikan model Product)

    def save(self, *args, **kwargs):
        try:
            self.full_clean()
        except ValidationError:
            # jika validasi gagal, biarkan propagate error ke caller (view)
            raise
        super().save(*args, **kwargs)