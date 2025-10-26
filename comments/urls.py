# comments/urls.py
from django.urls import path
from comments.views import create_comment, delete_comment, edit_reply, reply_to_comment, edit_comment, delete_reply

app_name = 'comments'

urlpatterns = [
    path('create-comment/', create_comment, name='create_comment'),
    path('edit/<uuid:comment_id>/', edit_comment, name='edit_comment'),
    path('delete/<uuid:comment_id>/', delete_comment, name='delete_comment'),
    path('reply/<uuid:comment_id>/', reply_to_comment, name='reply_comment'),
    path('reply/edit/<uuid:reply_id>/', edit_reply, name='edit_reply'),
    path('reply/delete/<uuid:reply_id>/', delete_reply, name='delete_reply'),
]