"""orders/admin.py — Admin config for orders."""

from django.contrib import admin

from .models import Cart, CartItem, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ["unit_price", "line_total"]
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "pk",
        "user",
        "status",
        "fulfilment",
        "total",
        "created_at",
    ]
    list_filter = ["status", "fulfilment"]
    search_fields = ["user__username", "user__email"]
    readonly_fields = ["subtotal", "total", "created_at", "updated_at"]
    inlines = [OrderItemInline]
    list_editable = ["status"]


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ["user", "item_count", "total", "updated_at"]
