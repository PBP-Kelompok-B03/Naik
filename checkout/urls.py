from django.urls import path
from .views import place_order, order_list_api, checkout_view, checkout_success, order_list

app_name = "checkout"

urlpatterns = [
    # WEB
    path("", checkout_view, name="checkout_view"),
    path("success/", checkout_success, name="checkout_success"),
    path("orders/", order_list, name="order_list"),

    # API
    path("api/place-order/", place_order, name="place_order"),
    path("api/orders/", order_list_api, name="order_list_api"),
]
