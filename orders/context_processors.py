"""
orders/context_processors.py

Makes the cart item count available in every template via {{ cart_count }}.
This avoids repeating the query in every individual view.
"""


def cart_count(request):
    """Inject cart item count into the global template context."""
    count = 0
    if request.user.is_authenticated:
        try:
            count = request.user.cart.item_count
        except Exception:
            count = 0
    return {"cart_count": count}
