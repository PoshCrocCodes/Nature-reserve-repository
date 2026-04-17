"""
URL configuration for Greenfield Local Hub.

Each functional area is handled by its own app with its own urls.py,
keeping the URL structure clean and maintainable.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    # Django admin (for superusers only)
    path("admin/", admin.site.urls),

    # Home page
    path("", include("products.urls")),

    # Accounts app — registration, login, profile, producer dashboard
    path("accounts/", include("accounts.urls")),

    # Products app — listing, detail, search, filter
    path("shop/", include("products.urls", namespace="products")),

    # Orders app — cart, checkout, order management, tracking
    path("orders/", include("orders.urls", namespace="orders")),

    # Reviews app — product and producer reviews
    path("reviews/", include("reviews.urls", namespace="reviews")),

    # Static informational pages
    path(
        "privacy-policy/",
        TemplateView.as_view(template_name="privacy_policy.html"),
        name="privacy_policy",
    ),
    path(
        "accessibility/",
        TemplateView.as_view(template_name="accessibility.html"),
        name="accessibility",
    ),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )
