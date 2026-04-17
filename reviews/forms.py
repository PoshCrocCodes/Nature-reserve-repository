"""reviews/forms.py — Forms for submitting product and producer reviews."""

from django import forms

from .models import ProducerReview, Review


class ReviewForm(forms.ModelForm):
    """Form for submitting a product review."""

    rating = forms.ChoiceField(
        choices=[(i, f"{i} star{'s' if i > 1 else ''}") for i in range(1, 6)],
        widget=forms.RadioSelect(attrs={"class": "star-radio"}),
        label="Your rating",
    )

    class Meta:
        model = Review
        fields = ["rating", "title", "body"]
        widgets = {
            "title": forms.TextInput(
                attrs={"placeholder": "Summarise your experience"}
            ),
            "body": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Tell other shoppers what you think...",
                }
            ),
        }

    def clean_rating(self):
        return int(self.cleaned_data["rating"])


class ProducerReviewForm(forms.ModelForm):
    """Form for submitting a producer review."""

    rating = forms.ChoiceField(
        choices=[(i, f"{i} star{'s' if i > 1 else ''}") for i in range(1, 6)],
        widget=forms.RadioSelect(attrs={"class": "star-radio"}),
        label="Your rating",
    )

    class Meta:
        model = ProducerReview
        fields = ["rating", "title", "body"]
        widgets = {
            "title": forms.TextInput(
                attrs={"placeholder": "Summarise your experience"}
            ),
            "body": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Share your experience with this producer...",
                }
            ),
        }

    def clean_rating(self):
        return int(self.cleaned_data["rating"])
