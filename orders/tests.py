"""
orders/tests.py

Test suite for the orders app.
Covers cart operations, order creation, tracking and cancellation.
"""

from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import ProducerProfile
from products.models import Category, Product

from .models import Cart, CartItem, Order, OrderItem


def make_product(name="Tomatoes", slug="tomatoes", price="1.00", stock=10):
    """Helper to create a product for testing."""
    user, _ = User.objects.get_or_create(
        username="order_producer", defaults={"password": "pass"}
    )
    producer, _ = ProducerProfile.objects.get_or_create(
        user=user,
        defaults={
            "business_name": "Order Test Farm",
            "slug": "order-test-farm",
            "description": "desc",
            "location": "Lancs",
        },
    )
    category, _ = Category.objects.get_or_create(
        name="Veg", defaults={"slug": "veg"}
    )
    return Product.objects.create(
        producer=producer,
        category=category,
        name=name,
        slug=slug,
        description="Fresh",
        price=Decimal(price),
        unit="kg",
        stock_quantity=stock,
        is_available=True,
    )


class CartModelTest(TestCase):
    """Unit tests for the Cart and CartItem models."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="cartuser", password="TestPass123!"
        )
        self.product = make_product()
        self.cart = Cart.objects.create(user=self.user)

    def test_cart_starts_empty(self):
        """A new cart has zero items and zero total."""
        self.assertEqual(self.cart.item_count, 0)
        self.assertEqual(self.cart.total, Decimal("0.00"))

    def test_add_item_updates_total(self):
        """Adding an item updates the cart total correctly."""
        CartItem.objects.create(
            cart=self.cart, product=self.product, quantity=2
        )
        self.assertEqual(self.cart.total, Decimal("2.00"))

    def test_item_count_reflects_quantity(self):
        """item_count sums quantities across all cart lines."""
        CartItem.objects.create(
            cart=self.cart, product=self.product, quantity=3
        )
        self.assertEqual(self.cart.item_count, 3)

    def test_cart_str(self):
        """Cart __str__ includes the username."""
        self.assertIn("cartuser", str(self.cart))


class OrderModelTest(TestCase):
    """Unit tests for the Order model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="orderuser", password="TestPass123!"
        )
        self.order = Order.objects.create(
            user=self.user,
            subtotal=Decimal("10.00"),
            total=Decimal("10.00"),
        )

    def test_order_default_status_is_pending(self):
        """A new order defaults to 'pending'."""
        self.assertEqual(self.order.status, "pending")

    def test_order_is_cancellable_when_pending(self):
        """Pending order is cancellable."""
        self.assertTrue(self.order.is_cancellable)

    def test_order_not_cancellable_when_preparing(self):
        """Order in 'preparing' status cannot be cancelled."""
        self.order.status = "preparing"
        self.assertFalse(self.order.is_cancellable)

    def test_progress_percentage_for_delivered(self):
        """Delivered order shows 100% progress."""
        self.order.status = "delivered"
        self.assertEqual(self.order.progress_percentage, 100)

    def test_progress_percentage_for_pending(self):
        """Pending order shows 0% progress."""
        self.assertEqual(self.order.progress_percentage, 0)

    def test_order_str(self):
        """Order __str__ includes the order pk and username."""
        self.assertIn("orderuser", str(self.order))
        self.assertIn(str(self.order.pk), str(self.order))


class AddToCartViewTest(TestCase):
    """Integration tests for adding items to the cart."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="addcartuser", password="TestPass123!"
        )
        self.client.login(username="addcartuser", password="TestPass123!")
        self.product = make_product(name="Leeks", slug="leeks", stock=5)

    def test_add_to_cart_creates_cart_item(self):
        """POSTing to add_to_cart creates a CartItem."""
        self.client.post(
            reverse("orders:add_to_cart", kwargs={"slug": "leeks"}),
            {"quantity": 2},
        )
        self.assertEqual(
            CartItem.objects.filter(
                cart__user=self.user, product=self.product
            ).count(),
            1,
        )

    def test_cannot_add_more_than_stock(self):
        """Attempting to add more than stock quantity is rejected."""
        response = self.client.post(
            reverse("orders:add_to_cart", kwargs={"slug": "leeks"}),
            {"quantity": 99},
        )
        self.assertFalse(
            CartItem.objects.filter(cart__user=self.user).exists()
        )

    def test_add_to_cart_requires_login(self):
        """Anonymous users are redirected to login."""
        self.client.logout()
        response = self.client.post(
            reverse("orders:add_to_cart", kwargs={"slug": "leeks"}),
            {"quantity": 1},
        )
        self.assertNotEqual(response.status_code, 200)


class CheckoutViewTest(TestCase):
    """Integration tests for the checkout flow."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="checkoutuser", password="TestPass123!"
        )
        self.client.login(username="checkoutuser", password="TestPass123!")
        self.product = make_product(
            name="Spinach", slug="spinach", stock=10
        )
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)

    def test_checkout_page_loads(self):
        """GET /orders/checkout/ returns 200."""
        response = self.client.get(reverse("orders:checkout"))
        self.assertEqual(response.status_code, 200)

    def test_successful_checkout_creates_order(self):
        """A valid POST to checkout creates an Order."""
        self.client.post(
            reverse("orders:checkout"),
            {"fulfilment": "collection", "notes": ""},
        )
        self.assertEqual(
            Order.objects.filter(user=self.user).count(), 1
        )

    def test_checkout_reduces_stock(self):
        """Placing an order reduces the product stock."""
        self.client.post(
            reverse("orders:checkout"),
            {"fulfilment": "collection"},
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 8)

    def test_checkout_awards_loyalty_points(self):
        """Placing an order awards loyalty points."""
        self.client.post(
            reverse("orders:checkout"),
            {"fulfilment": "collection"},
        )
        self.user.profile.refresh_from_db()
        self.assertGreater(self.user.profile.loyalty_points, 0)


class CancelOrderViewTest(TestCase):
    """Tests for order cancellation."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="canceluser", password="TestPass123!"
        )
        self.client.login(username="canceluser", password="TestPass123!")
        self.order = Order.objects.create(
            user=self.user,
            status="pending",
            subtotal=Decimal("5.00"),
            total=Decimal("5.00"),
        )

    def test_cancel_pending_order(self):
        """A pending order can be successfully cancelled."""
        self.client.post(
            reverse("orders:cancel_order", kwargs={"pk": self.order.pk})
        )
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "cancelled")

    def test_cannot_cancel_delivered_order(self):
        """A delivered order cannot be cancelled."""
        self.order.status = "delivered"
        self.order.save()
        self.client.post(
            reverse("orders:cancel_order", kwargs={"pk": self.order.pk})
        )
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "delivered")
