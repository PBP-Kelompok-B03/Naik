from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from decimal import Decimal
from main.models import Product
from checkout.models import Order, OrderItem
from checkout.forms import OrderForm

class CheckoutTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='hammam', password='test123')
        self.product = Product.objects.create(
            title="Sepatu Bola",
            price=Decimal('150000.00'),
            stock=10,
            count_sold=0,
            user=self.user
        )
        self.client.login(username='hammam', password='test123')

    def test_orderitem_total_price(self):
        order = Order.objects.create(
            user=self.user,
            total_price=Decimal('0'),
            address="Jl. Mawar",
        )
        item = OrderItem.objects.create(order=order, product=self.product, quantity=2, price=Decimal('150000.00'))
        self.assertEqual(item.get_total_price(), Decimal('300000.00'))
        self.assertIn(self.product.title, str(item))

    def test_checkout_get_page_loads(self):
        url = reverse('checkout:checkout_view') + f'?product_id={self.product.id}&quantity=2'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Checkout")
        self.assertIn("total_price", response.context)

    def test_checkout_post_ajax_success(self):
        url = reverse('checkout:checkout_view')
        data = {
            'product_id': self.product.id,
            'quantity': 2,
            'address': 'Jl. Anggrek No. 5',
            'payment_method': 'EWALLET',
            'shipping_type': 'CEPAT',
            'insurance': 'on',
            'note': 'Tolong cepat kirim ya'
        }
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result['status'], 'success')

        # Cek order di DB
        order = Order.objects.get(id=result['order_id'])
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.total_price, Decimal('150000.00')*2 + Decimal('10000.00') + Decimal('5000.00'))
        self.assertTrue(OrderItem.objects.filter(order=order).exists())

        # Cek stok berkurang
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)
        self.assertEqual(self.product.count_sold, 2)

    def test_checkout_post_ajax_insufficient_stock(self):
        self.product.stock = 1
        self.product.save()

        url = reverse('checkout:checkout_view')
        data = {
            'product_id': self.product.id,
            'quantity': 3,
            'address': 'Jl. Melati',
            'payment_method': 'COD',
        }
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')

    def test_checkout_success_view(self):
        # Buat order dummy
        order = Order.objects.create(user=self.user, total_price=Decimal('50000.00'), address="Jl. Mawar")
        OrderItem.objects.create(order=order, product=self.product, quantity=1, price=self.product.price)

        url = reverse('checkout:checkout_success')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pembayaran Berhasil")

    def test_order_list_view(self):
        Order.objects.create(user=self.user, total_price=Decimal('100000.00'), address="Jl. Kenanga")
        url = reverse('checkout:order_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Daftar Pesanan Saya")

    def test_order_form_valid_and_invalid(self):
        form = OrderForm(data={'address': 'Jl. Sakura', 'payment_method': 'COD'})
        self.assertTrue(form.is_valid())

        form_invalid = OrderForm(data={'address': ''})
        self.assertFalse(form_invalid.is_valid())
