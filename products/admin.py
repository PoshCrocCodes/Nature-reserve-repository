"""products/admin.py — Admin configuration for products."""

from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "producer",
        "category",
        "price",
        "unit",
        "stock_quantity",
        "is_available",
        "featured",
    ]
    list_filter = ["category", "is_available", "featured", "producer"]
    list_editable = ["stock_quantity", "is_available", "featured"]
    search_fields = ["name", "producer__business_name"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created_at", "updated_at"]
