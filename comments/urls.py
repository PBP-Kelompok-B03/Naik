# comments/urls.py
from django.urls import path
from comments.views import create_comment, delete_comment, edit_reply, reply_to_comment, edit_comment, delete_reply, \
    flutter_create_comment, flutter_edit_comment, flutter_delete_comment, flutter_reply_to_comment, flutter_edit_reply, flutter_delete_reply

app_name = 'comments'

urlpatterns = [
    # Web endpoints
    path('create-comment/', create_comment, name='create_comment'),
    path('edit/<uuid:comment_id>/', edit_comment, name='edit_comment'),
    path('delete/<uuid:comment_id>/', delete_comment, name='delete_comment'),
    path('reply/<uuid:comment_id>/', reply_to_comment, name='reply_comment'),
    path('reply/edit/<uuid:reply_id>/', edit_reply, name='edit_reply'),
    path('reply/delete/<uuid:reply_id>/', delete_reply, name='delete_reply'),
    
    # Flutter API endpoints
    path('api/flutter/create-comment/', flutter_create_comment, name='flutter_create_comment'),
    path('api/flutter/edit/<uuid:comment_id>/', flutter_edit_comment, name='flutter_edit_comment'),
    path('api/flutter/delete/<uuid:comment_id>/', flutter_delete_comment, name='flutter_delete_comment'),
    path('api/flutter/reply/<uuid:comment_id>/', flutter_reply_to_comment, name='flutter_reply_to_comment'),
    path('api/flutter/reply/edit/<uuid:reply_id>/', flutter_edit_reply, name='flutter_edit_reply'),
    path('api/flutter/reply/delete/<uuid:reply_id>/', flutter_delete_reply, name='flutter_delete_reply'),
]