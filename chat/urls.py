from django.urls import path
from . import views

app_name = "chat"

urlpatterns = [
    # list & create page (GET page is create_conversation_page; POST goes to create_conversation)
    path('', views.conversation_list, name='conversation_list'),
    path('new/', views.create_conversation_page, name='create_conversation_page'),  # new page to create
    path('create/', views.create_conversation, name='create_conversation'),  # POST target
    path('<uuid:convo_id>/', views.conversation_view, name='conversation_view'),

    # API endpoints
    path('api/create/', views.api_create_conversation, name='api_create_conversation'),
    path('api/<uuid:convo_id>/messages/', views.api_fetch_messages, name='api_fetch_messages'),
    path('api/<uuid:convo_id>/send/', views.api_send_message, name='api_send_message'),
    path('api/list/', views.api_conversation_list, name='api_conversation_list'),
]
