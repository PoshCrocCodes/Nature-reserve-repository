"""accounts/admin.py — Register models with the Django admin site."""

from django.contrib import admin

from .models import ProducerProfile, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "loyalty_tier", "loyalty_points", "gdpr_consent"]
    list_filter = ["loyalty_tier", "gdpr_consent", "marketing_opt_in"]
    search_fields = ["user__username", "user__email", "postcode"]
    readonly_fields = ["gdpr_consent_date", "created_at", "updated_at"]


@admin.register(ProducerProfile)
class ProducerProfileAdmin(admin.ModelAdmin):
    list_display = ["business_name", "user", "farming_method", "is_verified"]
    list_filter = ["farming_method", "is_verified"]
    search_fields = ["business_name", "location"]
    prepopulated_fields = {"slug": ("business_name",)}
    list_editable = ["is_verified"]
