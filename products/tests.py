"""
products/tests.py

Test suite for the products app.
Covers models, views, search and filtering.
"""

from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import ProducerProfile

from .models import Category, Product


class ProductModelTest(TestCase):
    """Unit tests for the Product model."""

    def setUp(self):
        user = User.objects.create_user(username="produser", password="pass")
        self.producer = ProducerProfile.objects.create(
            user=user,
            business_name="Test Farm",
            slug="test-farm",
            description="A test farm.",
            location="Lancashire",
        )
        self.category = Category.objects.create(
            name="Vegetables", slug="vegetables"
        )
        self.product = Product.objects.create(
            producer=self.producer,
            category=self.category,
            name="Carrots",
            slug="carrots",
            description="Fresh carrots",
            price=Decimal("1.50"),
            unit="kg",
            stock_quantity=20,
            is_available=True,
        )

    def test_product_str(self):
        """Product __str__ returns the product name."""
        self.assertEqual(str(self.product), "Carrots")

    def test_is_in_stock_true(self):
        """Product with stock > 0 reports as in stock."""
        self.assertTrue(self.product.is_in_stock)

    def test_is_in_stock_false_when_zero(self):
        """Product with stock 0 reports as out of stock."""
        self.product.stock_quantity = 0
        self.assertFalse(self.product.is_in_stock)

    def test_is_in_stock_false_when_unavailable(self):
        """Unavailable product reports as out of stock even with stock."""
        self.product.is_available = False
        self.assertFalse(self.product.is_in_stock)

    def test_average_rating_no_reviews(self):
        """Product with no reviews returns None for average rating."""
        self.assertIsNone(self.product.average_rating)

    def test_review_count_zero_initially(self):
        """Product starts with zero approved reviews."""
        self.assertEqual(self.product.review_count, 0)

    def test_get_absolute_url(self):
        """Product URL resolves correctly."""
        url = self.product.get_absolute_url()
        self.assertIn("carrots", url)


class CategoryModelTest(TestCase):
    """Unit tests for the Category model."""

    def test_category_str(self):
        cat = Category.objects.create(name="Dairy", slug="dairy")
        self.assertEqual(str(cat), "Dairy")

    def test_category_ordering(self):
        """Categories are ordered alphabetically by name."""
        Category.objects.create(name="Meat", slug="meat")
        Category.objects.create(name="Bakery", slug="bakery")
        names = list(Category.objects.values_list("name", flat=True))
        self.assertEqual(names, sorted(names))


class ProductListViewTest(TestCase):
    """Integration tests for the product listing view."""

    def setUp(self):
        self.client = Client()
        user = User.objects.create_user(username="viewuser", password="pass")
        producer = ProducerProfile.objects.create(
            user=user,
            business_name="View Farm",
            slug="view-farm",
            description="Desc",
            location="Lancs",
        )
        category = Category.objects.create(
            name="Fruit", slug="fruit"
        )
        Product.objects.create(
            producer=producer,
            category=category,
            name="Apples",
            slug="apples",
            description="Crunchy apples",
            price=Decimal("2.00"),
            unit="kg",
            stock_quantity=10,
            is_available=True,
        )

    def test_product_list_loads(self):
        """GET /products/ returns HTTP 200."""
        response = self.client.get(reverse("products:product_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "products/product_list.html")

    def test_search_returns_matching_product(self):
        """Searching for 'Apples' returns the Apples product."""
        response = self.client.get(
            reverse("products:product_list"), {"q": "Apples"}
        )
        self.assertContains(response, "Apples")

    def test_search_no_match_returns_empty(self):
        """Searching for a non-existent product shows no results."""
        response = self.client.get(
            reverse("products:product_list"), {"q": "NonExistentXYZ"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Apples")

    def test_category_filter(self):
        """Filtering by category slug returns correct products."""
        response = self.client.get(
            reverse("products:product_list"), {"category": "fruit"}
        )
        self.assertContains(response, "Apples")


class ProductDetailViewTest(TestCase):
    """Tests for the product detail page."""

    def setUp(self):
        self.client = Client()
        user = User.objects.create_user(username="detailuser", password="pass")
        producer = ProducerProfile.objects.create(
            user=user,
            business_name="Detail Farm",
            slug="detail-farm",
            description="Desc",
            location="Cheshire",
        )
        self.product = Product.objects.create(
            producer=producer,
            name="Potatoes",
            slug="potatoes",
            description="Fluffy potatoes",
            price=Decimal("0.99"),
            unit="kg",
            stock_quantity=50,
            is_available=True,
        )

    def test_product_detail_loads(self):
        """GET /products/{slug}/ returns HTTP 200."""
        response = self.client.get(
            reverse("products:product_detail", kwargs={"slug": "potatoes"})
        )
        self.assertEqual(response.status_code, 200)

    def test_product_detail_shows_price(self):
        """Product detail page displays the price."""
        response = self.client.get(
            reverse("products:product_detail", kwargs={"slug": "potatoes"})
        )
        self.assertContains(response, "0.99")

    def test_nonexistent_product_returns_404(self):
        """Requesting a non-existent slug returns 404."""
        response = self.client.get(
            reverse(
                "products:product_detail", kwargs={"slug": "does-not-exist"}
            )
        )
        self.assertEqual(response.status_code, 404)
