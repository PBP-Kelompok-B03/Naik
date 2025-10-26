# main/admin.py
from django.contrib import admin
from .models import Conversation, ConversationMessage

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_a', 'user_b', 'product_id', 'created_at', 'updated_at')
    search_fields = ('user_a__username', 'user_b__username', 'product_id')

@admin.register(ConversationMessage)
class ConversationMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'sender', 'created_at', 'is_read')
    search_fields = ('sender__username', 'content')
    list_filter = ('is_read',)
