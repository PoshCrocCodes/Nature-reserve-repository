"""
accounts/views.py

All views use Django class-based views (CBVs) for maintainability.
The producer dashboard is access-controlled to admin and producers only.

View Summary
------------
RegisterView          — New user registration with GDPR consent
CustomLoginView       — Login using the custom LoginForm
CustomLogoutView      — POST-based logout (CSRF protected)
ProfileView           — View and edit own profile + loyalty info
ProducerDashboardView — Manage stock, products, orders (producers only)
ProducerDetailView    — Public-facing producer page
ProducerListView      — All verified producers
"""

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from orders.models import Order
from products.models import Product

from .forms import (
    LoginForm,
    ProducerProfileForm,
    RegistrationForm,
    UserProfileForm,
    UserUpdateForm,
)
from .models import ProducerProfile, UserProfile


class RegisterView(CreateView):
    """Handle new user registration.

    On success, the user is logged in automatically and redirected home.
    GDPR consent is recorded with a timestamp.
    """

    form_class = RegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        user = form.save()
        # Record GDPR consent timestamp
        user.profile.gdpr_consent = True
        user.profile.gdpr_consent_date = timezone.now()
        user.profile.marketing_opt_in = form.cleaned_data.get(
            "marketing_opt_in", False
        )
        user.profile.save()
        login(self.request, user)
        messages.success(
            self.request,
            f"Welcome to Greenfield Local Hub, {user.first_name}! "
            "Your account has been created.",
        )
        return redirect(self.success_url)


class CustomLoginView(LoginView):
    """Login view using the custom styled form."""

    form_class = LoginForm
    template_name = "accounts/login.html"


class CustomLogoutView(LogoutView):
    """Logout using POST request (CSRF protected)."""

    next_page = reverse_lazy("home")


class ProfileView(LoginRequiredMixin, TemplateView):
    """Display the logged-in user's profile, loyalty status and order history."""

    template_name = "accounts/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["profile"] = user.profile
        context["recent_orders"] = (
            Order.objects.filter(user=user)
            .select_related("user")
            .prefetch_related("items__product")
            .order_by("-created_at")[:5]
        )
        # Points to next tier for progress bar
        context["points_to_next"] = user.profile.get_points_to_next_tier()
        return context


class EditProfileView(LoginRequiredMixin, TemplateView):
    """Allow a user to update their User and UserProfile details."""

    template_name = "accounts/edit_profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_form"] = UserUpdateForm(instance=self.request.user)
        context["profile_form"] = UserProfileForm(
            instance=self.request.user.profile
        )
        return context

    def post(self, request, *args, **kwargs):
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(
            request.POST, instance=request.user.profile
        )
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("accounts:profile")
        context = self.get_context_data()
        context["user_form"] = user_form
        context["profile_form"] = profile_form
        return self.render_to_response(context)


# ---------------------------------------------------------------------------
# PRODUCER DASHBOARD — admin and producers only
# ---------------------------------------------------------------------------

class ProducerRequiredMixin(UserPassesTestMixin):
    """Restrict access to admin users and verified producers."""

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (
            user.is_staff or hasattr(user, "producer_profile")
        )

    def handle_no_permission(self):
        messages.error(
            self.request,
            "You do not have permission to access the producer dashboard.",
        )
        return redirect("home")


class ProducerDashboardView(ProducerRequiredMixin, TemplateView):
    """Main producer dashboard — stock, orders, and product management."""

    template_name = "accounts/producer_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_staff:
            # Admins see all products and orders
            context["products"] = (
                Product.objects.select_related("producer", "category")
                .order_by("name")
            )
            context["recent_orders"] = (
                Order.objects.select_related("user")
                .prefetch_related("items__product")
                .order_by("-created_at")[:20]
            )
        else:
            producer = user.producer_profile
            context["producer"] = producer
            context["products"] = (
                Product.objects.filter(producer=producer)
                .select_related("category")
                .order_by("name")
            )
            context["recent_orders"] = (
                Order.objects.filter(items__product__producer=producer)
                .distinct()
                .select_related("user")
                .prefetch_related("items__product")
                .order_by("-created_at")[:20]
            )
        # Low-stock alert threshold
        context["low_stock_threshold"] = 5
        return context


class ProducerListView(ListView):
    """Public list of all verified producers."""

    model = ProducerProfile
    queryset = ProducerProfile.objects.filter(is_verified=True).order_by(
        "business_name"
    )
    template_name = "accounts/producer_list.html"
    context_object_name = "producers"
    paginate_by = 12


class ProducerDetailView(DetailView):
    """Public-facing page for a single producer."""

    model = ProducerProfile
    template_name = "accounts/producer_detail.html"
    context_object_name = "producer"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        producer = self.get_object()
        context["products"] = (
            Product.objects.filter(producer=producer, is_available=True)
            .select_related("category")
        )
        return context
