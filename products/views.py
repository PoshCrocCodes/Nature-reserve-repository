"""
products/views.py

Product listing, detail, search and home page views.
All class-based for maintainability.
"""

from django.db.models import Avg, Q
from django.views.generic import DetailView, ListView, TemplateView

from reviews.models import Review

from .models import Category, Product


class HomeView(TemplateView):
    """Homepage with hero banner, featured products and top-rated reviews."""

    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Featured products for the homepage grid
        context["featured_products"] = (
            Product.objects.filter(featured=True, is_available=True)
            .select_related("producer", "category")[:6]
        )
        # Top 3 approved reviews by highest rating for the homepage
        context["top_reviews"] = (
            Review.objects.filter(is_approved=True)
            .select_related("user", "product")
            .order_by("-rating", "-created_at")[:3]
        )
        context["categories"] = Category.objects.all()
        return context


class ProductListView(ListView):
    """Product catalogue with search, filter and sort functionality."""

    model = Product
    template_name = "products/product_list.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self):
        queryset = (
            Product.objects.filter(is_available=True)
            .select_related("producer", "category")
            .prefetch_related("reviews")
        )
        # --- Search ---
        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query)
                | Q(description__icontains=query)
                | Q(producer__business_name__icontains=query)
                | Q(category__name__icontains=query)
            )
        # --- Category filter ---
        category_slug = self.request.GET.get("category")
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        # --- Producer filter ---
        producer_slug = self.request.GET.get("producer")
        if producer_slug:
            queryset = queryset.filter(producer__slug=producer_slug)
        # --- In-stock filter ---
        in_stock = self.request.GET.get("in_stock")
        if in_stock == "true":
            queryset = queryset.filter(stock_quantity__gt=0)
        # --- Price range filter ---
        min_price = self.request.GET.get("min_price")
        max_price = self.request.GET.get("max_price")
        if min_price:
            try:
                queryset = queryset.filter(price__gte=float(min_price))
            except ValueError:
                pass
        if max_price:
            try:
                queryset = queryset.filter(price__lte=float(max_price))
            except ValueError:
                pass
        # --- Sort ---
        sort = self.request.GET.get("sort", "name")
        sort_options = {
            "name": "name",
            "price_asc": "price",
            "price_desc": "-price",
            "newest": "-created_at",
        }
        queryset = queryset.order_by(sort_options.get(sort, "name"))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        context["current_query"] = self.request.GET.get("q", "")
        context["current_category"] = self.request.GET.get("category", "")
        context["current_sort"] = self.request.GET.get("sort", "name")
        return context


class ProductDetailView(DetailView):
    """Full product detail page including traceability info and reviews."""

    model = Product
    template_name = "products/product_detail.html"
    context_object_name = "product"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return Product.objects.select_related(
            "producer", "category"
        ).prefetch_related("reviews__user")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        context["reviews"] = (
            product.reviews.filter(is_approved=True)
            .select_related("user")
            .order_by("-created_at")
        )
        context["related_products"] = (
            Product.objects.filter(
                category=product.category, is_available=True
            )
            .exclude(pk=product.pk)
            .select_related("producer")[:4]
        )
        # Check if the logged-in user has already reviewed this product
        if self.request.user.is_authenticated:
            context["user_has_reviewed"] = product.reviews.filter(
                user=self.request.user
            ).exists()
        return context
