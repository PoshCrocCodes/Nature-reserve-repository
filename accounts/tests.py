"""
accounts/tests.py

Test suite for the accounts app.
Covers models, forms, views and access control.
Minimum 6 test cases as per project requirements.
"""

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import ProducerProfile, UserProfile


class UserProfileModelTest(TestCase):
    """Tests for the UserProfile model and loyalty tier logic."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testfarmer",
            password="TestPass123!",
            first_name="Tom",
            last_name="Field",
            email="tom@example.com",
        )
        self.profile = self.user.profile  # Created via signal

    def test_profile_created_on_user_save(self):
        """A UserProfile is automatically created when a User is saved."""
        self.assertIsInstance(self.profile, UserProfile)
        self.assertEqual(self.profile.loyalty_points, 0)
        self.assertEqual(self.profile.loyalty_tier, "seedling")

    def test_loyalty_tier_updates_to_sapling(self):
        """Adding 500 points upgrades the tier to Sapling."""
        self.profile.loyalty_points = 500
        self.profile.update_loyalty_tier()
        self.assertEqual(self.profile.loyalty_tier, "sapling")

    def test_loyalty_tier_updates_to_oak(self):
        """Adding 1500 points upgrades the tier to Oak."""
        self.profile.loyalty_points = 1500
        self.profile.update_loyalty_tier()
        self.assertEqual(self.profile.loyalty_tier, "oak")

    def test_loyalty_tier_updates_to_elder(self):
        """Adding 3000 points upgrades the tier to Elder."""
        self.profile.loyalty_points = 3000
        self.profile.update_loyalty_tier()
        self.assertEqual(self.profile.loyalty_tier, "elder")

    def test_discount_percentage_for_elder(self):
        """Elder tier receives a 15% discount."""
        self.profile.loyalty_tier = "elder"
        self.assertEqual(self.profile.get_discount_percentage(), 15)

    def test_discount_percentage_for_seedling(self):
        """Seedling tier receives no discount."""
        self.assertEqual(self.profile.get_discount_percentage(), 0)

    def test_points_to_next_tier_from_seedling(self):
        """Seedling with 0 points needs 500 to reach Sapling."""
        self.profile.loyalty_points = 0
        self.assertEqual(self.profile.get_points_to_next_tier(), 500)

    def test_points_to_next_tier_is_zero_for_elder(self):
        """Elder tier has no next tier so returns 0."""
        self.profile.loyalty_tier = "elder"
        self.profile.loyalty_points = 3000
        self.assertEqual(self.profile.get_points_to_next_tier(), 0)

    def test_profile_str(self):
        """__str__ returns a human-readable representation."""
        self.assertIn("Tom Field", str(self.profile))


class RegistrationFormTest(TestCase):
    """Tests for the RegistrationForm validation."""

    def test_valid_registration_requires_gdpr_consent(self):
        """Registration without GDPR consent should be rejected."""
        from .forms import RegistrationForm

        data = {
            "first_name": "Jane",
            "last_name": "Green",
            "username": "janegreen",
            "email": "jane@example.com",
            "password1": "TestPass123!",
            "password2": "TestPass123!",
            "gdpr_consent": False,
        }
        form = RegistrationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("gdpr_consent", form.errors)

    def test_duplicate_email_rejected(self):
        """Registration with an already-used email should fail."""
        from .forms import RegistrationForm

        User.objects.create_user(
            username="existing", email="dupe@example.com", password="pass"
        )
        data = {
            "first_name": "New",
            "last_name": "User",
            "username": "newuser",
            "email": "dupe@example.com",
            "password1": "TestPass123!",
            "password2": "TestPass123!",
            "gdpr_consent": True,
        }
        form = RegistrationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)


class RegisterViewTest(TestCase):
    """Integration tests for the registration view."""

    def setUp(self):
        self.client = Client()
        self.url = reverse("accounts:register")

    def test_register_page_loads(self):
        """GET /accounts/register/ returns HTTP 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/register.html")

    def test_successful_registration_creates_user(self):
        """A valid POST creates a new User and UserProfile."""
        response = self.client.post(
            self.url,
            {
                "first_name": "Alice",
                "last_name": "Farm",
                "username": "alicefarm",
                "email": "alice@farm.co.uk",
                "password1": "SecurePass99!",
                "password2": "SecurePass99!",
                "gdpr_consent": True,
            },
        )
        self.assertEqual(User.objects.filter(username="alicefarm").count(), 1)


class LoginViewTest(TestCase):
    """Tests for the login view."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="loginuser", password="TestPass123!"
        )
        self.url = reverse("accounts:login")

    def test_login_page_loads(self):
        """GET /accounts/login/ returns HTTP 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_successful_login_redirects(self):
        """Valid credentials redirect to home."""
        response = self.client.post(
            self.url,
            {"username": "loginuser", "password": "TestPass123!"},
        )
        self.assertRedirects(response, "/")

    def test_invalid_login_shows_error(self):
        """Wrong credentials do not log the user in."""
        response = self.client.post(
            self.url,
            {"username": "loginuser", "password": "WrongPass!"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class ProducerDashboardAccessTest(TestCase):
    """Ensure the producer dashboard enforces access control."""

    def setUp(self):
        self.client = Client()
        self.dashboard_url = reverse("accounts:producer_dashboard")

        # Regular consumer
        self.consumer = User.objects.create_user(
            username="consumer", password="TestPass123!"
        )
        # Producer user
        self.producer_user = User.objects.create_user(
            username="producer", password="TestPass123!"
        )
        ProducerProfile.objects.create(
            user=self.producer_user,
            business_name="Green Acres",
            slug="green-acres",
            description="Fresh veg.",
            location="Lancashire",
        )

    def test_anonymous_user_cannot_access_dashboard(self):
        """Unauthenticated users are redirected to login."""
        response = self.client.get(self.dashboard_url)
        self.assertNotEqual(response.status_code, 200)

    def test_consumer_cannot_access_dashboard(self):
        """Regular consumers are denied access."""
        self.client.login(username="consumer", password="TestPass123!")
        response = self.client.get(self.dashboard_url)
        self.assertNotEqual(response.status_code, 200)

    def test_producer_can_access_dashboard(self):
        """A producer with a ProducerProfile can access the dashboard."""
        self.client.login(username="producer", password="TestPass123!")
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/producer_dashboard.html")
