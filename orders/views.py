from django.shortcuts import render
from django.http import HttpResponse
from carts.models import CartItem
from .forms import OrderForm
from .models import Order
from datetime import date
from django.shortcuts import redirect




def place_order(request, total=0, quantity=0):
    # öncelikli olarak cart_item var mı bakıyoruz.
    current_user = request.user
    # if cart count is less than or equal 0, than redirect to shop
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')

    grand_total = 0
    tax = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = (2 * total) / 100
    grand_total = total + tax
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # store all post data to order table
            data = Order()
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.email = form.cleaned_data['email']
            data.phone_number = form.cleaned_data['phone_number']
            data.city = form.cleaned_data['city']
            data.state = form.cleaned_data['state']
            data.country = form.cleaned_data['country']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.order_note = form.cleaned_data['order_note']

            data.order_total = grand_total
            data.tax = tax
            # data.ip = request.META.get('REMOTE_ADDR')

            data.user = current_user

            data.save()

            # Generate order number
            now = date.today()
            yr = int(now.strftime('%Y'))
            dt = int(now.strftime('%d'))
            mt = int(now.strftime('%m'))
            d = date(yr, mt, dt)
            current_date = d.strftime('%Y%m%d')  # 20211015
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()
            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)

            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
        
            }

            return render(request, 'orders/payments.html', context)
        else:
            return redirect('checkout')
    return HttpResponse('OK')


def payments(request):
    return render(request, 'orders/payments.html')
