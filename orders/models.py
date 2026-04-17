"""
orders/models.py

Models for the shopping cart, orders, order items and scheduling.
Order status drives the progress bar shown on the order tracking page.
"""

from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Order(models.Model):
    """A customer order — either for collection or delivery."""

    # --- Status choices drive the tracking progress bar ---
    STATUS_CHOICES = [
        ("pending", "Order Placed"),
        ("confirmed", "Confirmed"),
        ("preparing", "Being Prepared"),
        ("ready", "Ready for Collection / Dispatch"),
        ("out_for_delivery", "Out for Delivery"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    FULFILMENT_CHOICES = [
        ("collection", "Collection"),
        ("delivery", "Delivery"),
    ]

    # Progress bar steps (in order) — excludes 'cancelled'
    PROGRESS_STEPS = [
        "pending",
        "confirmed",
        "preparing",
        "ready",
        "out_for_delivery",
        "delivered",
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="orders"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    fulfilment = models.CharField(
        max_length=20, choices=FULFILMENT_CHOICES, default="collection"
    )

    # Delivery address (copied from profile at time of order — GDPR best practice)
    delivery_address_line_1 = models.CharField(max_length=255, blank=True)
    delivery_address_line_2 = models.CharField(max_length=255, blank=True)
    delivery_town_city = models.CharField(max_length=100, blank=True)
    delivery_county = models.CharField(max_length=100, blank=True)
    delivery_postcode = models.CharField(max_length=10, blank=True)

    # Scheduling — customer's preferred date/time slot
    scheduled_date = models.DateField(null=True, blank=True)
    scheduled_time_slot = models.CharField(max_length=50, blank=True)

    # Pricing
    subtotal = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    delivery_charge = models.DecimalField(
        max_digits=6, decimal_places=2, default=Decimal("0.00")
    )
    discount_amount = models.DecimalField(
        max_digits=6, decimal_places=2, default=Decimal("0.00")
    )
    total = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )

    # Loyalty points awarded for this order
    loyalty_points_awarded = models.PositiveIntegerField(default=0)
    # Discount code or loyalty tier used
    discount_code = models.CharField(max_length=50, blank=True)

    notes = models.TextField(
        blank=True, help_text="Any special instructions."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} — {self.user.username} ({self.status})"

    def get_absolute_url(self):
        return reverse("orders:order_detail", kwargs={"pk": self.pk})

    def calculate_totals(self):
        """Recalculate subtotal and total from line items."""
        self.subtotal = sum(item.line_total for item in self.items.all())
        self.total = self.subtotal + self.delivery_charge - self.discount_amount
        self.save(update_fields=["subtotal", "total"])

    @property
    def progress_step_index(self):
        """Return the 0-based index of the current status in PROGRESS_STEPS."""
        try:
            return self.PROGRESS_STEPS.index(self.status)
        except ValueError:
            return 0

    @property
    def progress_percentage(self):
        """Return percentage completion for the progress bar (0–100)."""
        steps = len(self.PROGRESS_STEPS)
        return round((self.progress_step_index / (steps - 1)) * 100)

    @property
    def is_cancellable(self):
        """Order can only be cancelled if still pending or confirmed."""
        return self.status in ("pending", "confirmed")


class OrderItem(models.Model):
    """A single line item within an order."""

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,  # Protect: keep historical order data
        related_name="order_items",
    )
    quantity = models.PositiveIntegerField(default=1)
    # Price frozen at time of purchase for audit / traceability
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        unique_together = [["order", "product"]]

    def __str__(self):
        return f"{self.quantity}x {self.product.name} (Order #{self.order.pk})"

    @property
    def line_total(self):
        """Total cost for this line item."""
        return self.unit_price * self.quantity


class Cart(models.Model):
    """Persistent shopping cart for authenticated users.

    Anonymous users' carts are stored in the session; this model
    persists the cart between sessions for logged-in users.
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="cart"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart — {self.user.username}"

    @property
    def total(self):
        """Sum of all cart item line totals."""
        return sum(item.line_total for item in self.cart_items.all())

    @property
    def item_count(self):
        """Total number of individual items in the cart."""
        return sum(item.quantity for item in self.cart_items.all())


class CartItem(models.Model):
    """A single product line in a cart."""

    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE, related_name="cart_items"
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="cart_items",
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = [["cart", "product"]]

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    @property
    def line_total(self):
        return self.product.price * self.quantity
