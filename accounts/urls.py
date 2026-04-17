"""accounts/urls.py — URL patterns for the accounts app."""

from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.CustomLogoutView.as_view(), name="logout"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("profile/edit/", views.EditProfileView.as_view(), name="edit_profile"),
    # Producer pages
    path(
        "dashboard/",
        views.ProducerDashboardView.as_view(),
        name="producer_dashboard",
    ),
    path(
        "producers/",
        views.ProducerListView.as_view(),
        name="producer_list",
    ),
    path(
        "producers/<slug:slug>/",
        views.ProducerDetailView.as_view(),
        name="producer_detail",
    ),
]
