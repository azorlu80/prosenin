from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product, Variation
from .models import Cart, CartItem
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required


# Create your views here.

def session(request):
    session = request.session.session_key
    if not session:
        session = request.session.create()
    return session

def add_cart(request, product_id):
    current_user = request.user
    # if user is authenticated
    if current_user.is_authenticated:
        product = Product.objects.get(id=product_id)
        product_variation = []
        if request.method == 'POST':
            for item in request.POST:
                key = item
                value = request.POST[key]
                try:
                    variation = Variation.objects.get(product=product, variation_category__iexact=key,
                                                      variation_value__iexact=value)
                    product_variation.append(variation)
                    # print(variation)
                except:
                    pass
            # color = request.POST['color']
            # size = request.POST['size']
            #     print(key, value)

        is_cart_item_exists = CartItem.objects.filter(product=product, user=current_user).exists()
        # ürün daha önce farklı bir vasyasyonla bile olsa chart ta var ise;
        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(product=product, user=current_user)
            existing_variation_list = []
            id = []
            for item in cart_item:
                existing_variation = item.variations.all()
                existing_variation_list.append(list(existing_variation))
                id.append(item.id)  # cartitem lerin id lerini listede topluyoruz
            if product_variation in existing_variation_list:
                # increase cartitem quantity
                index = existing_variation_list.index(product_variation)
                item_id = id[index]
                item = CartItem.objects.get(product=product, id=item_id)
                item.quantity += 1
                item.save()
            # post request ile gönderilen yeni vasyasyon deperinde ürün zaten chart ta yok ise;
            else:
                # create new cartitem
                item = CartItem.objects.create(
                    product=product,
                    quantity=1,
                    user=current_user,

                )
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()
        # ürün bir bir şekilde chart ta yok ise;
        else:
            cart_item = CartItem.objects.create(
                product=product,
                user=current_user,
                quantity=1
            )
            if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)

            cart_item.save()
        return redirect("cart")

    # if user in not authenticated
    else:

        product = Product.objects.get(id=product_id)
        product_variation = []
        if request.method == 'POST':
            for item in request.POST:
                key = item
                value = request.POST[key]
                try:
                    variation = Variation.objects.get(product=product, variation_category__iexact=key,
                                                      variation_value__iexact=value)
                    product_variation.append(variation)
                    # print(variation)
                except:
                    pass
            # color = request.POST['color']
            # size = request.POST['size']
            #     print(key, value)

        try:
            cart = Cart.objects.get(cart_id=session(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(
                cart_id=session(request)
            )
        cart.save()

        is_cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists()
        # ürün daha önce farklı bir vasyasyonla bile olsa chart ta var ise;
        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(product=product, cart=cart)
            # existing_variations --- database --done
            # current variation --- product_variations
            # item_id ---- database
            existing_variation_list = []
            id = []
            for item in cart_item:
                existing_variation = item.variations.all()
                existing_variation_list.append(list(existing_variation))
                id.append(item.id)  # cartitem lerin id lerini listede topluyoruz
            # print(existing_variation_list)
            # post request ile gönderilen yeni vasyasyon deperinde ürün zaten chart ta var ise
            if product_variation in existing_variation_list:
                # increase cartitem quantity
                index = existing_variation_list.index(product_variation)
                item_id = id[index]
                item = CartItem.objects.get(product=product, id=item_id)
                item.quantity += 1
                item.save()
            # post request ile gönderilen yeni vasyasyon deperinde ürün zaten chart ta yok ise;
            else:
                # create new cartitem
                item = CartItem.objects.create(
                    product=product,
                    quantity=1,
                    cart=cart,

                )
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()
        # ürün bir bir şekilde chart ta yok ise;
        else:
            cart_item = CartItem.objects.create(
                product=product,
                cart=cart,
                quantity=1
            )
            if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)

            cart_item.save()
        return redirect("cart")


def decrease_cart_item(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id=session(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
    return redirect('cart')


# aynı üründen birden fazla varyasyon listede olduğu için hangi ürün ve hangi varyasyonun dilineceğini bilgisini almamız
# gerekiyor.

def remove_cart_item(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        cart_item = CartItem.objects.filter(product=product, user=request.user, id=cart_item_id)
    else:
        cart = Cart.objects.get(cart_id=session(request))
        cart_item = CartItem.objects.filter(product=product, cart=cart, id=cart_item_id)
    cart_item.delete()

    return redirect('cart')


def cart(request, total=0, quantity=0, cart_items=None, tax=0, grand_total=0):
    try:
        # tax = 0
        # grand_total = 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=session(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            # quantity += cart_item.quantity
        tax = (18 * total) / 100
        grand_total = total + tax

    except ObjectDoesNotExist:
        pass
    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,

    }
    return render(request, 'store/cart.html', context)


@login_required(login_url='login')
def checkout(request, total=0, quantity=0, cart_items=None, tax=0, grand_total=0):
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=session(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        # tax = 0
        # grand_total = 0

        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            # quantity += cart_item.quantity
        tax = (18 * total) / 100
        grand_total = total + tax

    except ObjectDoesNotExist:
        pass
    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,

    }

    return render(request, 'store/checkout.html', context)