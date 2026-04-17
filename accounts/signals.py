"""
accounts/signals.py

Django signals to automatically create a UserProfile whenever a new User
is saved. This keeps the profile creation logic in one place.
"""

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile when a new User account is registered."""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Ensure the UserProfile is saved when the User is saved."""
    if hasattr(instance, "profile"):
        instance.profile.save()
