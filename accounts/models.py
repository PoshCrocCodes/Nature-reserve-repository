"""
accounts/models.py

Models for user accounts, profiles, and the GLH loyalty scheme.
One-to-one UserProfile extends Django's built-in User model so
third-party maintainers can still use the standard auth system.
"""

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    """Extended profile attached to each registered user.

    Stores delivery address, phone number, loyalty points and GDPR consent.
    Automatically created via a post_save signal in accounts/signals.py.
    """

    LOYALTY_TIERS = [
        ("seedling", "Seedling"),
        ("sapling", "Sapling"),
        ("oak", "Oak"),
        ("elder", "Elder"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    phone_number = models.CharField(max_length=20, blank=True)
    address_line_1 = models.CharField(max_length=255, blank=True)
    address_line_2 = models.CharField(max_length=255, blank=True)
    town_city = models.CharField(max_length=100, blank=True)
    county = models.CharField(max_length=100, blank=True)
    postcode = models.CharField(max_length=10, blank=True)

    # Loyalty scheme
    loyalty_points = models.PositiveIntegerField(default=0)
    loyalty_tier = models.CharField(
        max_length=20,
        choices=LOYALTY_TIERS,
        default="seedling",
    )

    # GDPR — explicit opt-in required at registration
    gdpr_consent = models.BooleanField(default=False)
    gdpr_consent_date = models.DateTimeField(null=True, blank=True)

    # Marketing opt-in (separate from GDPR consent — PECR compliance)
    marketing_opt_in = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"Profile — {self.user.get_full_name() or self.user.username}"

    def update_loyalty_tier(self):
        """Recalculate the user's loyalty tier based on current points."""
        points = self.loyalty_points
        if points >= 3000:
            self.loyalty_tier = "elder"
        elif points >= 1500:
            self.loyalty_tier = "oak"
        elif points >= 500:
            self.loyalty_tier = "sapling"
        else:
            self.loyalty_tier = "seedling"
        self.save(update_fields=["loyalty_tier"])

    def get_discount_percentage(self):
        """Return the discount percentage the user's tier entitles them to."""
        tier_discounts = {
            "seedling": 0,
            "sapling": 5,
            "oak": 10,
            "elder": 15,
        }
        return tier_discounts.get(self.loyalty_tier, 0)

    def get_points_to_next_tier(self):
        """Return how many more points are needed to reach the next tier."""
        tier_thresholds = {
            "seedling": 500,
            "sapling": 1500,
            "oak": 3000,
            "elder": None,
        }
        threshold = tier_thresholds.get(self.loyalty_tier)
        if threshold is None:
            return 0
        return max(0, threshold - self.loyalty_points)


class ProducerProfile(models.Model):
    """Additional information for users who are food producers / farmers.

    A producer account is a standard User with is_producer=True on their
    UserProfile, plus this linked ProducerProfile for business details.
    Only accessible by admin and the producer themselves.
    """

    FARMING_METHODS = [
        ("organic", "Organic"),
        ("conventional", "Conventional"),
        ("biodynamic", "Biodynamic"),
        ("free_range", "Free Range"),
        ("regenerative", "Regenerative Agriculture"),
        ("mixed", "Mixed Methods"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="producer_profile",
    )
    business_name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(
        help_text="Tell customers about your farm and produce."
    )
    farming_method = models.CharField(
        max_length=30,
        choices=FARMING_METHODS,
        default="conventional",
    )
    location = models.CharField(
        max_length=200,
        help_text="General area (e.g. 'Near Chorley, Lancashire')",
    )
    # IMAGE: Producer profile photo or farm image.
    # Replace with a licensed image from Unsplash (unsplash.com) or Pexels (pexels.com) — both free for commercial use.
    profile_image = models.ImageField(
        upload_to="producers/",
        blank=True,
        null=True,
    )
    website_url = models.URLField(blank=True)
    is_verified = models.BooleanField(
        default=False,
        help_text="Admin-verified producer.",
    )
    joined = models.DateField(default=timezone.now)

    class Meta:
        verbose_name = "Producer Profile"
        verbose_name_plural = "Producer Profiles"
        ordering = ["business_name"]

    def __str__(self):
        return self.business_name
