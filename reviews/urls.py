"""reviews/urls.py — URL patterns for the reviews app."""

from django.urls import path

from . import views

app_name = "reviews"

urlpatterns = [
    path(
        "product/<slug:slug>/",
        views.SubmitProductReviewView.as_view(),
        name="submit_product_review",
    ),
    path(
        "producer/<slug:slug>/",
        views.SubmitProducerReviewView.as_view(),
        name="submit_producer_review",
    ),
]
