"""
products/models.py

Core product catalogue models.
Products are linked to a Producer (a local farmer/food producer) and a
Category. Stock levels support the producer dashboard and traceability.
"""

from django.db import models
from django.urls import reverse


class Category(models.Model):
    """Product category (e.g. Vegetables, Dairy, Meat, Bakery)."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    # IMAGE: Category icon or banner.
    # Replace with a licensed image from Unsplash or Pexels (free for commercial use).
    image = models.ImageField(upload_to="categories/", blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("products:product_list") + f"?category={self.slug}"


class Product(models.Model):
    """A product listed in the GLH shop.

    Includes pricing, availability, stock tracking and traceability fields.
    """

    UNIT_CHOICES = [
        ("each", "Each"),
        ("kg", "Per kg"),
        ("100g", "Per 100g"),
        ("litre", "Per litre"),
        ("500ml", "Per 500ml"),
        ("dozen", "Per dozen"),
        ("bunch", "Per bunch"),
        ("loaf", "Per loaf"),
        ("jar", "Per jar"),
        ("bottle", "Per bottle"),
    ]

    # Linked to the ProducerProfile, not the User directly
    producer = models.ForeignKey(
        "accounts.ProducerProfile",
        on_delete=models.CASCADE,
        related_name="products",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name="products",
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    # Transparent pricing as required
    price = models.DecimalField(max_digits=8, decimal_places=2)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default="each")
    # Stock control
    stock_quantity = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    # Traceability fields
    origin = models.CharField(
        max_length=200,
        blank=True,
        help_text="Where this product was grown / produced.",
    )
    certifications = models.CharField(
        max_length=300,
        blank=True,
        help_text="e.g. Organic Soil Association, Red Tractor",
    )
    # IMAGE: Main product photo.
    # Replace with a licensed image from Unsplash or Pexels (free for commercial use).
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    featured = models.BooleanField(
        default=False,
        help_text="Show on the homepage featured section.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("products:product_detail", kwargs={"slug": self.slug})

    @property
    def is_in_stock(self):
        """Return True if the product has stock available."""
        return self.stock_quantity > 0 and self.is_available

    @property
    def average_rating(self):
        """Calculate average rating from approved reviews."""
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            total = sum(r.rating for r in reviews)
            return round(total / reviews.count(), 1)
        return None

    @property
    def review_count(self):
        """Count of approved reviews."""
        return self.reviews.filter(is_approved=True).count()
