"""
reviews/views.py

Class-based views for submitting and displaying product and producer reviews.
Reviews go to a moderation queue before appearing publicly.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView, View

from accounts.models import ProducerProfile
from products.models import Product

from .forms import ProducerReviewForm, ReviewForm
from .models import ProducerReview, Review


class SubmitProductReviewView(LoginRequiredMixin, View):
    """Handle product review form submission."""

    def post(self, request, *args, **kwargs):
        product = get_object_or_404(Product, slug=kwargs["slug"])

        # Prevent duplicate reviews
        if Review.objects.filter(user=request.user, product=product).exists():
            messages.warning(
                request,
                "You have already submitted a review for this product.",
            )
            return redirect("products:product_detail", slug=product.slug)

        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.product = product
            review.save()
            messages.success(
                request,
                "Thank you for your review! It will appear once approved.",
            )
        else:
            messages.error(
                request,
                "There was a problem with your review. Please try again.",
            )
        return redirect("products:product_detail", slug=product.slug)


class SubmitProducerReviewView(LoginRequiredMixin, View):
    """Handle producer review form submission."""

    def post(self, request, *args, **kwargs):
        producer = get_object_or_404(ProducerProfile, slug=kwargs["slug"])

        if ProducerReview.objects.filter(
            user=request.user, producer=producer
        ).exists():
            messages.warning(
                request,
                "You have already submitted a review for this producer.",
            )
            return redirect(
                "accounts:producer_detail", slug=producer.slug
            )

        form = ProducerReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.producer = producer
            review.save()
            messages.success(
                request,
                "Thank you! Your review will appear once it has been approved.",
            )
        else:
            messages.error(
                request,
                "There was a problem with your review. Please try again.",
            )
        return redirect("accounts:producer_detail", slug=producer.slug)
