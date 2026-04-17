"""products/urls.py — URL patterns for the products app."""

from django.urls import path

from . import views

app_name = "products"

urlpatterns = [
    # Homepage — served from products app
    path("", views.HomeView.as_view(), name="home"),
    # Product catalogue
    path("products/", views.ProductListView.as_view(), name="product_list"),
    # Single product
    path(
        "products/<slug:slug>/",
        views.ProductDetailView.as_view(),
        name="product_detail",
    ),
]
