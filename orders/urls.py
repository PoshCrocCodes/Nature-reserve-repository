"""orders/urls.py — URL patterns for the orders app."""

from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("cart/", views.CartView.as_view(), name="cart"),
    path(
        "cart/add/<slug:slug>/",
        views.AddToCartView.as_view(),
        name="add_to_cart",
    ),
    path(
        "cart/update/<int:pk>/",
        views.UpdateCartView.as_view(),
        name="update_cart",
    ),
    path("checkout/", views.CheckoutView.as_view(), name="checkout"),
    path("my-orders/", views.OrderListView.as_view(), name="order_list"),
    path(
        "my-orders/<int:pk>/",
        views.OrderDetailView.as_view(),
        name="order_detail",
    ),
    path(
        "my-orders/<int:pk>/cancel/",
        views.CancelOrderView.as_view(),
        name="cancel_order",
    ),
    path(
        "my-orders/<int:pk>/reschedule/",
        views.RescheduleOrderView.as_view(),
        name="reschedule_order",
    ),
]
