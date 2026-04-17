"""
reviews/models.py

Product and producer reviews with moderation support.
Reviews must be approved before they appear publicly (prevents spam/abuse).
"""

from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Review(models.Model):
    """A customer review for a product.

    Must be approved by an admin or producer before being displayed.
    One review per user per product enforced at the DB level.
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="reviews"
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1 (poor) to 5 (excellent)",
    )
    title = models.CharField(max_length=150)
    body = models.TextField()
    is_approved = models.BooleanField(
        default=False,
        help_text="Only approved reviews are shown publicly.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        # One review per user per product
        unique_together = [["user", "product"]]
        verbose_name = "Product Review"

    def __str__(self):
        return f"{self.rating}★ — {self.product.name} by {self.user.username}"


class ProducerReview(models.Model):
    """A customer review for a producer / farm.

    Separate from product reviews so producers can track their
    reputation independently of individual products.
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="producer_reviews"
    )
    producer = models.ForeignKey(
        "accounts.ProducerProfile",
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    title = models.CharField(max_length=150)
    body = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = [["user", "producer"]]
        verbose_name = "Producer Review"

    def __str__(self):
        return (
            f"{self.rating}★ — {self.producer.business_name} "
            f"by {self.user.username}"
        )
