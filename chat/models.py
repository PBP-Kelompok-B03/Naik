from django.db import models
from django.contrib.auth.models import User
import uuid

class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_a = models.ForeignKey(User, related_name="conversations_a", on_delete=models.CASCADE)
    user_b = models.ForeignKey(User, related_name="conversations_b", on_delete=models.CASCADE)
    product_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def participants(self):
        return [self.user_a, self.user_b]

    def __str__(self):
        return f"Percakapan antara {self.user_a.username} dan {self.user_b.username}"
    
    def unread_count_for(self, user):
        """Hitung jumlah pesan yang belum dibaca oleh user tertentu."""
        return self.messages.filter(is_read=False).exclude(sender=user).count()


class ConversationMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, related_name="messages", on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(blank=True)   # allow empty if image-only
    image = models.ImageField(upload_to='chat_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        text = (self.content or "")[:20]
        if self.image and not text:
            text = "[image]"
        return f"{self.sender.username}: {text}"
