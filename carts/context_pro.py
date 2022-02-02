from .models import Cart, CartItem
from .views import session


# setting dosyasında templates altında context processors kısmına eklenir.bu sayede budaraki sorguyu istediğinimiz template de kullanabiliriz.

def counter(request):
    cart_count = 0
    if 'admin' in request.path:
        return {}
    else:
        try:
            cart = Cart.objects.filter(cart_id=session(request))
            if request.user.is_authenticated:
                cart_items = CartItem.objects.all().filter(user=request.user)
            else:
                cart_items = CartItem.objects.all().filter(cart=cart[:1])

            for cart_item in cart_items:
                cart_count += cart_item.quantity

        except Cart.DoesNotExist:
            cart_count = 0

    return dict(cart_count=cart_count)
