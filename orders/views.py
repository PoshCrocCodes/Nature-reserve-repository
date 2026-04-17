"""
orders/views.py

Class-based views for cart management, checkout, order history,
order detail with progress bar tracking, and order scheduling.
"""

from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from products.models import Product

from .models import Cart, CartItem, Order, OrderItem

# Delivery charge applied to all delivery orders
DELIVERY_CHARGE = Decimal("3.95")
# Loyalty points per £1 spent
POINTS_PER_POUND = 10


# ---------------------------------------------------------------------------
# CART VIEWS
# ---------------------------------------------------------------------------

class CartView(LoginRequiredMixin, TemplateView):
    """Display the current user's shopping cart."""

    template_name = "orders/cart.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        context["cart"] = cart
        context["cart_items"] = (
            cart.cart_items.select_related("product__producer")
        )
        context["delivery_charge"] = DELIVERY_CHARGE
        return context


class AddToCartView(LoginRequiredMixin, View):
    """Add a product to the cart or increment quantity."""

    def post(self, request, *args, **kwargs):
        product = get_object_or_404(Product, slug=kwargs["slug"])
        quantity = int(request.POST.get("quantity", 1))

        if quantity < 1:
            messages.error(request, "Quantity must be at least 1.")
            return redirect("products:product_detail", slug=product.slug)

        if quantity > product.stock_quantity:
            messages.error(
                request,
                f"Sorry, only {product.stock_quantity} available.",
            )
            return redirect("products:product_detail", slug=product.slug)

        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, product=product, defaults={"quantity": quantity}
        )
        if not created:
            new_qty = cart_item.quantity + quantity
            if new_qty > product.stock_quantity:
                messages.warning(
                    request,
                    f"You already have {cart_item.quantity} in your cart. "
                    f"Maximum available is {product.stock_quantity}.",
                )
            else:
                cart_item.quantity = new_qty
                cart_item.save()

        messages.success(
            request, 
         f'"{product.name}" has been added to your basket.'
        )
        return redirect("orders:cart")


class UpdateCartView(LoginRequiredMixin, View):
    """Update quantity of a cart item or remove it."""

    def post(self, request, *args, **kwargs):
        cart_item = get_object_or_404(
            CartItem, pk=kwargs["pk"], cart__user=request.user
        )
        action = request.POST.get("action")
        if action == "remove":
            cart_item.delete()
            messages.info(request, "Item removed from your basket.")
        else:
            quantity = int(request.POST.get("quantity", 1))
            if quantity < 1:
                cart_item.delete()
                messages.info(request, "Item removed from your basket.")
            elif quantity > cart_item.product.stock_quantity:
                messages.error(
                    request,
                    f"Only {cart_item.product.stock_quantity} available.",
                )
            else:
                cart_item.quantity = quantity
                cart_item.save()
        return redirect("orders:cart")


# ---------------------------------------------------------------------------
# CHECKOUT VIEWS
# ---------------------------------------------------------------------------

class CheckoutView(LoginRequiredMixin, TemplateView):
    """Display the checkout form with delivery/collection options."""

    template_name = "orders/checkout.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        profile = self.request.user.profile
        context["cart"] = cart
        context["cart_items"] = cart.cart_items.select_related("product")
        context["profile"] = profile
        context["delivery_charge"] = DELIVERY_CHARGE
        context["discount_percentage"] = profile.get_discount_percentage()
        # Available time slots for scheduling
        context["time_slots"] = [
            "09:00 – 11:00",
            "11:00 – 13:00",
            "13:00 – 15:00",
            "15:00 – 17:00",
        ]
        return context

    def post(self, request, *args, **kwargs):
        """Place the order."""
        cart, _ = Cart.objects.get_or_create(user=request.user)
        if not cart.cart_items.exists():
            messages.error(request, "Your basket is empty.")
            return redirect("orders:cart")

        profile = request.user.profile
        fulfilment = request.POST.get("fulfilment", "collection")
        scheduled_date = request.POST.get("scheduled_date") or None
        scheduled_slot = request.POST.get("time_slot", "")
        notes = request.POST.get("notes", "")

        subtotal = cart.total
        delivery = DELIVERY_CHARGE if fulfilment == "delivery" else Decimal("0.00")
        discount_pct = profile.get_discount_percentage()
        discount_amount = (subtotal * Decimal(discount_pct)) / Decimal("100")
        total = subtotal + delivery - discount_amount

        # Create the Order
        order = Order.objects.create(
            user=request.user,
            fulfilment=fulfilment,
            delivery_address_line_1=profile.address_line_1,
            delivery_address_line_2=profile.address_line_2,
            delivery_town_city=profile.town_city,
            delivery_county=profile.county,
            delivery_postcode=profile.postcode,
            scheduled_date=scheduled_date,
            scheduled_time_slot=scheduled_slot,
            subtotal=subtotal,
            delivery_charge=delivery,
            discount_amount=discount_amount,
            total=total,
            notes=notes,
        )

        # Create OrderItems and reduce stock
        for cart_item in cart.cart_items.select_related("product"):
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                unit_price=cart_item.product.price,
            )
            # Reduce stock
            product = cart_item.product
            product.stock_quantity = max(
                0, product.stock_quantity - cart_item.quantity
            )
            product.save(update_fields=["stock_quantity"])

        # Award loyalty points (1 point per 10p = 10 per £1)
        points = int(total * POINTS_PER_POUND)
        profile.loyalty_points += points
        profile.update_loyalty_tier()
        order.loyalty_points_awarded = points
        order.save(update_fields=["loyalty_points_awarded"])

        # Clear the cart
        cart.cart_items.all().delete()

        messages.success(
            request,
            f"🎉 Order #{order.pk} placed successfully! "
            f"You earned {points} loyalty points.",
        )
        return redirect("orders:order_detail", pk=order.pk)


# ---------------------------------------------------------------------------
# ORDER MANAGEMENT VIEWS
# ---------------------------------------------------------------------------

class OrderListView(LoginRequiredMixin, ListView):
    """List all orders for the logged-in user."""

    model = Order
    template_name = "orders/order_list.html"
    context_object_name = "orders"
    paginate_by = 10

    def get_queryset(self):
        return (
            Order.objects.filter(user=self.request.user)
            .prefetch_related("items__product")
            .order_by("-created_at")
        )


class OrderDetailView(LoginRequiredMixin, DetailView):
    """Single order detail with progress bar and tracking info."""

    model = Order
    template_name = "orders/order_detail.html"
    context_object_name = "order"

    def get_queryset(self):
        # Users can only see their own orders
        return Order.objects.filter(user=self.request.user).prefetch_related(
            "items__product__producer"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.get_object()
        context["progress_steps"] = Order.PROGRESS_STEPS
        context["progress_step_labels"] = {
            step: label for step, label in Order.STATUS_CHOICES
        }
        context["current_step_index"] = order.progress_step_index
        context["progress_percentage"] = order.progress_percentage
        return context


class CancelOrderView(LoginRequiredMixin, View):
    """Allow users to cancel a pending or confirmed order."""

    def post(self, request, *args, **kwargs):
        order = get_object_or_404(
            Order, pk=kwargs["pk"], user=request.user
        )
        if order.is_cancellable:
            order.status = "cancelled"
            order.save(update_fields=["status"])
            # Return stock
            for item in order.items.select_related("product"):
                product = item.product
                product.stock_quantity += item.quantity
                product.save(update_fields=["stock_quantity"])
            # Reverse loyalty points
            profile = request.user.profile
            profile.loyalty_points = max(
                0, profile.loyalty_points - order.loyalty_points_awarded
            )
            profile.update_loyalty_tier()
            messages.success(
                request, f"Order #{order.pk} has been cancelled."
            )
        else:
            messages.error(
                request,
                "This order can no longer be cancelled. "
                "Please contact us for assistance.",
            )
        return redirect("orders:order_detail", pk=order.pk)


class RescheduleOrderView(LoginRequiredMixin, View):
    """Allow users to reschedule a pending order."""

    def post(self, request, *args, **kwargs):
        order = get_object_or_404(
            Order, pk=kwargs["pk"], user=request.user
        )
        if order.status not in ("pending", "confirmed"):
            messages.error(request, "This order cannot be rescheduled.")
            return redirect("orders:order_detail", pk=order.pk)

        new_date = request.POST.get("scheduled_date")
        new_slot = request.POST.get("time_slot", "")
        order.scheduled_date = new_date or None
        order.scheduled_time_slot = new_slot
        order.save(update_fields=["scheduled_date", "scheduled_time_slot"])
        messages.success(request, "Your order has been rescheduled.")
        return redirect("orders:order_detail", pk=order.pk)
