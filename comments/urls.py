# comments/urls.py
from django.urls import path
from comments.views import create_comment, reply_to_comment, edit_comment

app_name = 'comments'

urlpatterns = [
    path('create-comment/', create_comment, name='create_comment'),
    path('reply/<int:comment_id>/', reply_to_comment, name='reply_comment'),
    path('edit/<int:comment_id>/', edit_comment, name='edit_comment'),
]