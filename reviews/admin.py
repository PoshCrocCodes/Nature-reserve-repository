"""reviews/admin.py — Admin config with moderation actions."""

from django.contrib import admin

from .models import ProducerReview, Review


def approve_reviews(modeladmin, request, queryset):
    """Bulk action: approve selected reviews."""
    queryset.update(is_approved=True)


approve_reviews.short_description = "Approve selected reviews"


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = [
        "product",
        "user",
        "rating",
        "title",
        "is_approved",
        "created_at",
    ]
    list_filter = ["is_approved", "rating"]
    search_fields = ["user__username", "product__name", "title"]
    list_editable = ["is_approved"]
    actions = [approve_reviews]


@admin.register(ProducerReview)
class ProducerReviewAdmin(admin.ModelAdmin):
    list_display = [
        "producer",
        "user",
        "rating",
        "is_approved",
        "created_at",
    ]
    list_filter = ["is_approved", "rating"]
    list_editable = ["is_approved"]
    actions = [approve_reviews]
