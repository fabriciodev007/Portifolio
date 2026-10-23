def cart_count(request):
    cart = request.session.get('cart', []) if hasattr(request, 'session') else []
    if isinstance(cart, dict):
        count = sum(cart.values())
    elif isinstance(cart, list):
        count = sum(item.get('quantity', 0) for item in cart)
    else:
        count = 0
    return {'cart_count': count}
