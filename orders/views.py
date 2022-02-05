from django.shortcuts import render
from django.http import HttpResponse
from carts.models import CartItem
from .forms import OrderForm
from .models import Order,Payment, OrderProduct
from datetime import date
from django.shortcuts import redirect
import json
from store.models import Product
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

def place_order(request, total=0, quantity=0):
    # öncelikli olarak cart_item var mı bakıyoruz.
    current_user = request.user
    # if cart count is less than or equal 0, than redirect to shop
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')
    else:
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
                data.user = current_user
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
                data.ip = request.META.get('REMOTE_ADDR')

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
                order = Order.objects.get(
                    user=current_user, is_ordered=False, order_number=order_number)

                context = {
                    'order': order,
                    'cart_items': cart_items,
                    'total': total,
                    'tax': tax,
                    'grand_total': grand_total,

                }
                return render(request, 'orders/payments.html', context)
            else:
                #TODO:form invalid error handle
                pass
        else:
            return redirect('checkout')
    return HttpResponse(("OK"))

def payments(request):
    #TODO:json olarak donen degeri goster.fecth
    body = json.loads(request.body)
    #order amount ayni zamanda paypaldan donen json dosyasindan da alinabilir di?
    order = Order.objects.get(user=request.user, is_ordered=False, order_number=body["orderID"])
    # print(body)
    #TODO:store transaction details inside Payment model
    payment = Payment(
        user = request.user,
        payment_id = body["transID"],
        payment_method=body["payment_method"],
        amount_payment=order.order_total,
        status=body["status"],
        
    )
    payment.save()
    order.payment = payment
    order.is_ordered = True
    order.save()

    #move the cart items to order product table

    cart_items = CartItem.objects.filter(user=request.user)
    for item in cart_items:
        orderproduct = OrderProduct()

        orderproduct.order_id = order.id
        orderproduct.payment = payment
        orderproduct.user_id = request.user.id
        orderproduct.product_id = item.product_id
        orderproduct.quantity = item.quantity
        orderproduct.ordered = True
        orderproduct.product_price = item.product.price
        orderproduct.save() 

        #add product variations to orderproduct table
        cart_item = CartItem.objects.get(id=item.id)
        product_variation = cart_item.variations.all()
        orderproduct = OrderProduct.objects.get(id=orderproduct.id)
        orderproduct.variations.set(product_variation)
        orderproduct.save()



    #reduce quantity of the sold procusts

        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()



    #clear cart

    CartItem.objects.filter(user=request.user).delete()

    #TODO:send order recivede email to customer

    mail_subject = 'Thank you for your order'
    message = render_to_string('orders/order_recieved_email', {
                'user': request.user,
                "order": order,
                
    })
    to_mail = request.user.email
    send_email = EmailMessage(mail_subject, message, to=[to_mail])
    send_email.send()

    #send order number transaction id back to sendData method via json responce

    
    return render(request, 'orders/payments.html')
