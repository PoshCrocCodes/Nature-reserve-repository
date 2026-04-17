"""
reviews/tests.py

Test suite for the reviews app.
Covers model validation, duplicate prevention, moderation and form handling.
"""

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import ProducerProfile
from products.models import Category, Product

from .forms import ReviewForm
from .models import ProducerReview, Review


def make_review_fixtures():
    """Helper: create a user, producer and product for review tests."""
    producer_user = User.objects.create_user(
        username="review_producer", password="pass"
    )
    producer = ProducerProfile.objects.create(
        user=producer_user,
        business_name="Review Farm",
        slug="review-farm",
        description="desc",
        location="Lancs",
    )
    category = Category.objects.create(name="Herbs", slug="herbs")
    product = Product.objects.create(
        producer=producer,
        category=category,
        name="Basil",
        slug="basil",
        description="Fresh basil",
        price="1.20",
        unit="bunch",
        stock_quantity=10,
        is_available=True,
    )
    return producer_user, producer, product


class ReviewModelTest(TestCase):
    """Unit tests for the Review model."""

    def setUp(self):
        self.producer_user, self.producer, self.product = (
            make_review_fixtures()
        )
        self.reviewer = User.objects.create_user(
            username="reviewer1", password="pass"
        )

    def test_review_str(self):
        """Review __str__ contains the rating and product name."""
        review = Review.objects.create(
            user=self.reviewer,
            product=self.product,
            rating=4,
            title="Great",
            body="Really good basil.",
        )
        self.assertIn("4", str(review))
        self.assertIn("Basil", str(review))

    def test_review_defaults_to_not_approved(self):
        """New reviews are unapproved by default."""
        review = Review.objects.create(
            user=self.reviewer,
            product=self.product,
            rating=5,
            title="Brilliant",
            body="Loved it.",
        )
        self.assertFalse(review.is_approved)

    def test_duplicate_review_raises_integrity_error(self):
        """A user cannot leave two reviews for the same product."""
        from django.db import IntegrityError

        Review.objects.create(
            user=self.reviewer,
            product=self.product,
            rating=3,
            title="OK",
            body="Fine.",
        )
        with self.assertRaises(IntegrityError):
            Review.objects.create(
                user=self.reviewer,
                product=self.product,
                rating=4,
                title="Good",
                body="Actually good.",
            )

    def test_product_review_count_only_counts_approved(self):
        """product.review_count only counts approved reviews."""
        Review.objects.create(
            user=self.reviewer,
            product=self.product,
            rating=4,
            title="OK",
            body="Nice.",
            is_approved=False,
        )
        self.assertEqual(self.product.review_count, 0)


class ReviewFormTest(TestCase):
    """Validation tests for the ReviewForm."""

    def test_valid_review_form(self):
        """A properly completed review form is valid."""
        form = ReviewForm(
            data={"rating": "5", "title": "Excellent", "body": "Loved it!"}
        )
        self.assertTrue(form.is_valid())

    def test_review_form_missing_body(self):
        """Review form without body text is invalid."""
        form = ReviewForm(data={"rating": "3", "title": "OK", "body": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("body", form.errors)

    def test_review_form_rating_out_of_range(self):
        """Rating outside 1–5 is rejected."""
        form = ReviewForm(
            data={"rating": "6", "title": "Test", "body": "Too high."}
        )
        self.assertFalse(form.is_valid())


class SubmitProductReviewViewTest(TestCase):
    """Integration tests for the product review submission view."""

    def setUp(self):
        self.client = Client()
        _, _, self.product = make_review_fixtures()
        self.reviewer = User.objects.create_user(
            username="viewreviewer", password="TestPass123!"
        )
        self.client.login(username="viewreviewer", password="TestPass123!")
        self.url = reverse(
            "reviews:submit_product_review",
            kwargs={"slug": self.product.slug},
        )

    def test_submit_review_creates_record(self):
        """POSTing a valid review creates a Review object."""
        self.client.post(
            self.url,
            {"rating": "4", "title": "Tasty", "body": "Really nice basil."},
        )
        self.assertEqual(
            Review.objects.filter(
                user=self.reviewer, product=self.product
            ).count(),
            1,
        )

    def test_duplicate_review_rejected(self):
        """A second review submission for the same product is rejected."""
        Review.objects.create(
            user=self.reviewer,
            product=self.product,
            rating=3,
            title="Good",
            body="Good basil.",
        )
        self.client.post(
            self.url,
            {"rating": "5", "title": "Changed", "body": "Reconsidered."},
        )
        # Still only one review
        self.assertEqual(
            Review.objects.filter(
                user=self.reviewer, product=self.product
            ).count(),
            1,
        )

    def test_review_requires_login(self):
        """Anonymous users cannot submit reviews."""
        self.client.logout()
        response = self.client.post(
            self.url,
            {"rating": "5", "title": "Great", "body": "Wonderful."},
        )
        self.assertNotEqual(response.status_code, 200)


class ProducerReviewModelTest(TestCase):
    """Unit tests for the ProducerReview model."""

    def setUp(self):
        self.producer_user, self.producer, _ = make_review_fixtures()
        self.reviewer = User.objects.create_user(
            username="prodreviewer", password="pass"
        )

    def test_producer_review_str(self):
        """ProducerReview __str__ contains the producer business name."""
        review = ProducerReview.objects.create(
            user=self.reviewer,
            producer=self.producer,
            rating=5,
            title="Brilliant farm",
            body="Always fresh.",
        )
        self.assertIn("Review Farm", str(review))

    def test_producer_review_default_not_approved(self):
        """New producer reviews are unapproved by default."""
        review = ProducerReview.objects.create(
            user=self.reviewer,
            producer=self.producer,
            rating=4,
            title="Good",
            body="Happy with the produce.",
        )
        self.assertFalse(review.is_approved)
