import io
import json
import uuid
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Conversation, ConversationMessage


class ChatViewsTests(TestCase):
    def setUp(self):
        # Buat dua user
        self.user1 = User.objects.create_user(username="alice", password="pass123")
        self.user2 = User.objects.create_user(username="bob", password="pass123")
        self.client = Client()
        self.client.login(username="alice", password="pass123")

        # Buat percakapan
        self.convo = Conversation.objects.create(user_a=self.user1, user_b=self.user2)
        self.msg = ConversationMessage.objects.create(
            conversation=self.convo,
            sender=self.user2,
            content="Hello Alice!"
        )

    def test_create_conversation_page(self):
        url = reverse("chat:create_conversation_page")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "create_chat.html")

    def test_conversation_list_view(self):
        url = reverse("chat:conversation_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat_list.html")
        self.assertIn("conversations", response.context)
        self.assertGreaterEqual(len(response.context["conversations"]), 1)

    def test_conversation_view_access_and_render(self):
        url = reverse("chat:conversation_view", args=[self.convo.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat_room.html")

    def test_conversation_view_forbidden_for_non_participant(self):
        user3 = User.objects.create_user(username="charlie", password="pass123")
        self.client.login(username="charlie", password="pass123")
        url = reverse("chat:conversation_view", args=[self.convo.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_create_conversation_via_post_username(self):
        url = reverse("chat:create_conversation")
        response = self.client.post(url, {"username": "bob"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Conversation.objects.exists())

    def test_create_conversation_with_self_fails(self):
        url = reverse("chat:create_conversation")
        response = self.client.post(url, {"username": "alice"})
        self.assertEqual(response.status_code, 400)

    def test_create_conversation_user_not_found(self):
        url = reverse("chat:create_conversation")
        response = self.client.post(url, {"username": "nonexist"})
        self.assertEqual(response.status_code, 400)

    def test_api_fetch_messages_valid(self):
        url = reverse("chat:api_fetch_messages", args=[self.convo.pk])
        response = self.client.get(url)
        data = response.json()
        self.assertIn("messages", data)
        self.assertEqual(response.status_code, 200)

    def test_api_fetch_messages_forbidden(self):
        user3 = User.objects.create_user(username="eve", password="pass123")
        self.client.login(username="eve", password="pass123")
        url = reverse("chat:api_fetch_messages", args=[self.convo.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_api_send_message_valid(self):
        url = reverse("chat:api_send_message", args=[self.convo.pk])
        response = self.client.post(url, {"content": "Hai!"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ConversationMessage.objects.filter(content="Hai!").exists())

    def test_api_send_message_with_image(self):
        url = reverse("chat:api_send_message", args=[self.convo.pk])
        image = SimpleUploadedFile("test.jpg", b"fakeimage", content_type="image/jpeg")
        response = self.client.post(url, {"image": image})
        self.assertEqual(response.status_code, 200)
        self.assertIn("ok", response.json())

    def test_api_send_message_empty_error(self):
        url = reverse("chat:api_send_message", args=[self.convo.pk])
        response = self.client.post(url, {"content": ""})
        self.assertEqual(response.status_code, 400)

    def test_api_send_message_forbidden(self):
        user3 = User.objects.create_user(username="james", password="pass123")
        self.client.login(username="james", password="pass123")
        url = reverse("chat:api_send_message", args=[self.convo.pk])
        response = self.client.post(url, {"content": "Hey"})
        self.assertEqual(response.status_code, 403)

    def test_api_create_conversation_form(self):
        url = reverse("chat:api_create_conversation")
        response = self.client.post(url, {"username": "bob"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("ok", response.json())

    def test_api_create_conversation_json_body(self):
        url = reverse("chat:api_create_conversation")
        body = json.dumps({"user_id": self.user2.id})
        response = self.client.post(url, body, content_type="application/json")
        self.assertEqual(response.status_code, 200)

    def test_api_create_conversation_missing_fields(self):
        url = reverse("chat:api_create_conversation")
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 400)

    def test_api_create_conversation_self_error(self):
        url = reverse("chat:api_create_conversation")
        body = json.dumps({"username": "alice"})
        response = self.client.post(url, body, content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_api_create_conversation_user_not_found(self):
        url = reverse("chat:api_create_conversation")
        body = json.dumps({"username": "ghost"})
        response = self.client.post(url, body, content_type="application/json")
        self.assertEqual(response.status_code, 404)


class ConversationModelTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="alice", password="123")
        self.user2 = User.objects.create_user(username="bob", password="123")
        self.convo = Conversation.objects.create(user_a=self.user1, user_b=self.user2)

    def test_str_representation(self):
        self.assertIn("alice", str(self.convo))

    def test_participants(self):
        parts = self.convo.participants()
        self.assertIn(self.user1, parts)
        self.assertIn(self.user2, parts)

    def test_unread_count_for(self):
        msg1 = ConversationMessage.objects.create(
            conversation=self.convo, sender=self.user1, content="Hai"
        )
        msg2 = ConversationMessage.objects.create(
            conversation=self.convo, sender=self.user2, content="Hai"
        )
        self.assertEqual(self.convo.unread_count_for(self.user1), 1)
        msg2.is_read = True
        msg2.save()
        self.assertEqual(self.convo.unread_count_for(self.user1), 0)

    def test_message_str_with_image(self):
        msg = ConversationMessage.objects.create(
            conversation=self.convo, sender=self.user1
        )
        self.assertIn("alice", str(msg))
