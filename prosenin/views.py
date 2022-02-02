from django.shortcuts import render
from store.models import Product
from django.http import HttpResponse
# test için
from carts.models import Cart, CartItem
from carts.views import session

import json


def home(request):
    products = Product.objects.all().filter(is_available=True)
    context = {
        'products': products,
    }
    return render(request, 'home.html', context)


def test(request):
    return render(request, 'test.html')

    # cart_items_queryset = CartItem.objects.filter(user=request.user)
    # serializer = CartItemSerializer(cart_items_queryset)
    # json = JSONRenderer().render(serializer)
    #
    # return HttpResponse(json)
