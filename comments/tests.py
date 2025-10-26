# comments/tests.py
from decimal import Decimal
import uuid

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from main.models import Product, Profile
from checkout.models import Order, OrderItem
from comments.models import Comment, Reply


class CommentsClientTests(TestCase):
    def setUp(self):
        self.client = Client()

        # users
        self.buyer = User.objects.create_user(username='buyer', password='pwd')
        self.seller = User.objects.create_user(username='seller', password='pwd')

        # ensure profile roles (signal in main may create a Profile; set role explicitly)
        Profile.objects.filter(user=self.buyer).update(role='buyer')
        Profile.objects.filter(user=self.seller).update(role='seller')

        # product by seller
        self.product = Product.objects.create(
            id=uuid.uuid4(),
            user=self.seller,
            title='Sepatu Test',
            price=Decimal('100000'),
            category="Men's Shoes",
            stock=10,
        )

        # order by buyer with allowed status
        self.order = Order.objects.create(
            id=uuid.uuid4(),
            user=self.buyer,
            total_price=Decimal('0'),
            address='Jl Test',
            status='PAID',
        )

        # order item
        self.order_item = OrderItem.objects.create(
            id=uuid.uuid4(),
            order=self.order,
            product=self.product,
            quantity=1,
            price=self.product.price,
        )

    def test_create_comment_creates(self):
        self.client.login(username='buyer', password='pwd')
        url = reverse('comments:create_comment')
        data = {'order_item_id': str(self.order_item.id), 'content': 'Bagus', 'rating': 4}
        resp = self.client.post(url, data)
        # create_comment redirects (302) after success
        self.assertEqual(resp.status_code, 302)
        qs = Comment.objects.filter(order_item=self.order_item, author=self.buyer)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().content, 'Bagus')

    def test_create_comment_updates_existing(self):
        # create initial comment
        Comment.objects.create(
            id=uuid.uuid4(),
            author=self.buyer,
            product=self.product,
            order_item=self.order_item,
            content='awal',
            rating=3
        )

        self.client.login(username='buyer', password='pwd')
        url = reverse('comments:create_comment')
        data = {'order_item_id': str(self.order_item.id), 'content': 'diubah', 'rating': 5}
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 302)
        qs = Comment.objects.filter(order_item=self.order_item, author=self.buyer)
        self.assertEqual(qs.count(), 1)
        updated = qs.first()
        self.assertEqual(updated.content, 'diubah')
        self.assertEqual(updated.rating, 5)

    def test_create_comment_forbidden_if_not_owner(self):
        # create an order belonging to seller (not buyer)
        other_order = Order.objects.create(
            id=uuid.uuid4(), user=self.seller, total_price=Decimal('0'), address='X', status='PAID'
        )
        other_item = OrderItem.objects.create(
            id=uuid.uuid4(), order=other_order, product=self.product, quantity=1, price=self.product.price
        )

        self.client.login(username='buyer', password='pwd')
        url = reverse('comments:create_comment')
        data = {'order_item_id': str(other_item.id), 'content': 'x', 'rating': 4}
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(Comment.objects.filter(order_item=other_item).exists())

    def test_edit_comment_forbidden_and_success(self):
        # comment authored by seller
        c = Comment.objects.create(
            id=uuid.uuid4(), author=self.seller, product=self.product,
            order_item=self.order_item, content='init', rating=3
        )

        url_edit = reverse('comments:edit_comment', args=[str(c.id)])

        # buyer tries to edit -> forbidden
        self.client.login(username='buyer', password='pwd')
        resp = self.client.post(url_edit, {'content': 'x', 'rating': '4'})
        self.assertEqual(resp.status_code, 403)

        # seller edits -> success
        self.client.login(username='seller', password='pwd')
        resp2 = self.client.post(url_edit, {'content': 'edited', 'rating': '5'})
        self.assertEqual(resp2.status_code, 302)
        c.refresh_from_db()
        self.assertEqual(c.content, 'edited')
        self.assertEqual(c.rating, 5)

    def test_delete_comment_forbidden_and_success(self):
        c = Comment.objects.create(
            id=uuid.uuid4(), author=self.seller, product=self.product,
            order_item=self.order_item, content='to be removed', rating=2
        )
        url_delete = reverse('comments:delete_comment', args=[str(c.id)])

        # buyer tries to delete -> forbidden
        self.client.login(username='buyer', password='pwd')
        resp = self.client.post(url_delete)
        self.assertEqual(resp.status_code, 403)

        # seller deletes
        self.client.login(username='seller', password='pwd')
        resp2 = self.client.post(url_delete)
        self.assertEqual(resp2.status_code, 302)
        self.assertFalse(Comment.objects.filter(pk=c.id).exists())

    def test_reply_to_comment_validation_and_save(self):
        c = Comment.objects.create(
            id=uuid.uuid4(), author=self.buyer, product=self.product,
            order_item=self.order_item, content='komentar', rating=4
        )

        url_reply = reverse('comments:reply_comment', args=[str(c.id)])

        # GET not allowed -> calling GET via client should return 405 or 400 depending on view; view returns 400
        self.client.login(username='seller', password='pwd')
        resp_get = self.client.get(url_reply)
        self.assertIn(resp_get.status_code, (400, 405))

        # POST empty content -> should not create reply
        resp_empty = self.client.post(url_reply, {'content': ''})
        self.assertEqual(Reply.objects.filter(comment=c).count(), 0)

        # POST valid content by seller -> create reply
        resp_ok = self.client.post(url_reply, {'content': 'balas seller'})
        self.assertEqual(resp_ok.status_code, 302)
        self.assertEqual(Reply.objects.filter(comment=c).count(), 1)

    def test_edit_reply_forbidden_and_success(self):
        c = Comment.objects.create(
            id=uuid.uuid4(), author=self.buyer, product=self.product,
            order_item=self.order_item, content='komentar', rating=4
        )
        r = Reply.objects.create(id=uuid.uuid4(), comment=c, author=self.seller, content='awal')

        url_edit = reverse('comments:edit_reply', args=[str(r.id)])

        # buyer tries to edit -> forbidden
        self.client.login(username='buyer', password='pwd')
        resp = self.client.post(url_edit, {'content': 'x'})
        self.assertEqual(resp.status_code, 403)

        # author edits
        self.client.login(username='seller', password='pwd')
        resp2 = self.client.post(url_edit, {'content': 'edited reply'})
        self.assertEqual(resp2.status_code, 302)
        r.refresh_from_db()
        self.assertEqual(r.content, 'edited reply')

    def test_delete_reply_forbidden_and_success(self):
        c = Comment.objects.create(
            id=uuid.uuid4(), author=self.buyer, product=self.product,
            order_item=self.order_item, content='komentar', rating=4
        )
        r = Reply.objects.create(id=uuid.uuid4(), comment=c, author=self.seller, content='hapus ini')

        url_delete = reverse('comments:delete_reply', args=[str(r.id)])

        # buyer tries delete
        self.client.login(username='buyer', password='pwd')
        resp = self.client.post(url_delete)
        self.assertEqual(resp.status_code, 403)

        # author deletes
        self.client.login(username='seller', password='pwd')
        resp2 = self.client.post(url_delete)
        self.assertEqual(resp2.status_code, 302)
        self.assertFalse(Reply.objects.filter(pk=r.id).exists())