from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import RegistrationForm
from .models import Account
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
# account verification
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

from carts.views import session
from carts.models import Cart, CartItem
from django.shortcuts import get_object_or_404

import requests


# Create your views here.

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        # print(form.errors)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split('@')[0]
            user = Account.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                email=email,
                username=username,
                password=password
            )
            user.phone_number = phone_number
            print(user.first_name)
            user.save()
            # account verification
            current_site = get_current_site(request)
            mail_subject = 'Please activate your account'
            message = render_to_string('accounts/account_verification_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_mail = email
            send_email = EmailMessage(mail_subject, message, to=[to_mail])
            send_email.send()
            # smtp ayar?? yapal??m
            #  messages.success(request, 'Please check your email and active to your account')
            return redirect('/accounts/login/?command=verification&email=' + email)

    else:
        # eger get request g??nderilirse RegistrationForm render edilecek.

        form = RegistrationForm()

    context = {
        'form': form,
    }
    return render(request, 'accounts/register.html', context)


def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(email=email, password=password)
        if user is not None:
            try:
                cart_id = session(request)
                cart = Cart.objects.get(cart_id=cart_id)
                is_cart_item_exists = CartItem.objects.filter(cart_id=cart.id).exists()
                if is_cart_item_exists:
                    # cart ile cart_item leri buluyoruz ki bu durumda user daha sisteme giri?? yapmad??g?? durumlardaki
                    cart_item = CartItem.objects.filter(cart=cart)
                    # iki adet listemiz oluyor 1- product_list digeri existing_variation_list
                    product_variation = []
                    for item in cart_item:
                        variation = item.variations.all()
                        product_variation.append(list(variation))

                        # get the cart items from the user to access his product variations
                    # user forengkey ile cart_item leri buluyoruz ki bu durumda sisteme login olduktan sonraki
                    cart_item = CartItem.objects.filter(user=user)
                    existing_variation_list = []
                    id = []
                    for item in cart_item:
                        existing_variation = item.variations.all()
                        existing_variation_list.append(list(existing_variation))
                        id.append(item.id)  # cartitem lerin id lerini listede topluyoruz
                    # iki k??menin kar????alt??r??lmas??
                    # zaten varsa sadece say??s??n?? artt??r.
                    for pr in product_variation:
                        if pr in existing_variation_list:
                            index = existing_variation_list.index(pr)
                            item_id = id[index]
                            item = CartItem.objects.get(id=item_id)
                            item.quantity += 1
                            item.user = user
                            item.save()
                        else:
                            cart_item = CartItem.objects.filter(cart=cart)
                            for item in cart_item:
                                item.user = user
                                item.save()

                    # cart item degerlerini gezip user a atama yap
                    # for item in cart_item:
                    #     item.user = user
                    #     item.save()
            except:
                pass
            auth.login(request, user)
            messages.success(request, 'You are now logged in')
            # get request path and decide render page install requests library
            url = request.META.get('HTTP_REFERER')  # buradaki built-in request lib.
            print('url :'+url)    
            try:
                print('parse url :'+requests.utils.urlparse(url))
                query = requests.utils.urlparse(url).query
                print('query : '+query )
                # buras?? biraz opsiyonel direk y??nlendirmede yap??labilir.
                params = dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    nextpage = params['next']
                    return redirect(nextpage)
                else:
                    pass
            except:
                return redirect('dashboard')
        else:
            messages.error(request, 'invalid login credentials')
            return redirect('login')

    return render(request, 'accounts/login.html')


# login url tan??mlanmas?? manuel get requestlerde y??nlendirilecek url dir.

@login_required(login_url='login')
def logout(request):
    auth.logout(request)
    messages.success(request, 'You are logged out')
    return redirect('login')


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Congratulations your account is activated')
        return redirect('login')
    else:
        messages.error(request, 'Invalid activation link')
        return redirect('register')

    return HttpResponse('OK')


@login_required(login_url='login')
def dashboard(request):
    return render(request, 'accounts/dashboard.html')


def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        if Account.objects.filter(email=email).exists():
            #veri tabaninda bu mail adresi kayitlimi kontrol et.kayitli ise :
            #bu email adresinde kayitli kullaniciyi bul
            user = Account.objects.get(email__exact=email)  # exact case sensitive iexact non case sensitive

            # reset password email hazirla
            current_site = get_current_site(request)
            mail_subject = 'Please reset your password'
            message = render_to_string('accounts/reset_password_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_mail = email
            send_email = EmailMessage(mail_subject, message, to=[to_mail])
            send_email.send()

            messages.success(request, 'Password reset email has been sent to your email address')
            return redirect('login')
        else:
            messages.error(request, 'Account does not exist.')
            return redirect('forgotPassword')
    return render(request, 'accounts/forgotPassword.html')


def resetpassword_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, 'Please reset your password')

        return redirect('resetpassword')

    else:
        messages.error(request, 'This is has been expired')
        return redirect('login')

    return HttpResponse('OK')


def resetpassword(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            # validasyon do??ru ise session uid degerini set etmi??tik geri al??yoruz.
            try:
                uid = request.session.get('uid')
                user = Account.objects.get(pk=uid)
                user.set_password(password)
                user.save()
                messages.success(request, 'Your password has changed')
                return redirect('login')
            except:
                return HttpResponse('Hey bro!!')    
        else:
            messages.error(request, 'Password do not match!')
            return redirect('resetpassword')
    else:
        return render(request, 'accounts/resetpassword.html')
