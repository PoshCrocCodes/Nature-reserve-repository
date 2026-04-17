"""
accounts/forms.py

Forms for user registration, login, and profile management.
All forms include WCAG-compliant labels and ARIA helpers.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

from .models import UserProfile, ProducerProfile


class RegistrationForm(UserCreationForm):
    """Extended registration form that captures name and GDPR consent."""

    first_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(
            attrs={"placeholder": "First name", "aria-label": "First name"}
        ),
    )
    last_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(
            attrs={"placeholder": "Last name", "aria-label": "Last name"}
        ),
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "placeholder": "Email address",
                "aria-label": "Email address",
            }
        ),
    )
    gdpr_consent = forms.BooleanField(
        required=True,
        label=(
            "I agree to the storage and processing of my personal data "
            "in accordance with the Privacy Policy (required)"
        ),
        error_messages={
            "required": (
                "You must accept the privacy policy to create an account."
            )
        },
    )
    marketing_opt_in = forms.BooleanField(
        required=False,
        label=(
            "I would like to receive news and special offers from "
            "Greenfield Local Hub (optional)"
        ),
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
            "password1",
            "password2",
        ]

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "An account with this email address already exists."
            )
        return email


class LoginForm(AuthenticationForm):
    """Custom login form with accessible placeholders."""

    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Username",
                "aria-label": "Username",
                "autofocus": True,
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Password",
                "aria-label": "Password",
            }
        )
    )


class UserProfileForm(forms.ModelForm):
    """Form for editing the user's delivery address and preferences."""

    class Meta:
        model = UserProfile
        fields = [
            "phone_number",
            "address_line_1",
            "address_line_2",
            "town_city",
            "county",
            "postcode",
            "marketing_opt_in",
        ]
        widgets = {
            "phone_number": forms.TextInput(
                attrs={"placeholder": "e.g. 07700 900000"}
            ),
            "address_line_1": forms.TextInput(
                attrs={"placeholder": "House number and street"}
            ),
            "postcode": forms.TextInput(attrs={"placeholder": "e.g. PR7 1AA"}),
        }


class UserUpdateForm(forms.ModelForm):
    """Form for updating basic User model fields (name, email)."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]

    def clean_email(self):
        email = self.cleaned_data.get("email")
        # Exclude the current user when checking for duplicate emails
        if (
            User.objects.filter(email=email)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise forms.ValidationError(
                "Another account is already using this email address."
            )
        return email


class ProducerProfileForm(forms.ModelForm):
    """Form for producers to update their business profile."""

    class Meta:
        model = ProducerProfile
        fields = [
            "business_name",
            "description",
            "farming_method",
            "location",
            "profile_image",
            "website_url",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
        }
