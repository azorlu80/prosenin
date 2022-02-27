from django.shortcuts import render, get_object_or_404
from .models import Product, ReviewRating
from category.models import Category
from carts.views import session
from carts.models import CartItem
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
# Create your views here.
from django.http import HttpResponse
from django.db.models import Q
from .forms import ReviewForm
from django.contrib import messages
from django.shortcuts import redirect
from orders.models import OrderProduct
def store(request, category_slug=None):
    categories = None
    products = None

    if category_slug is not None:
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=categories, is_available=True)
        paginator = Paginator(products, 2)
        page = request.GET.get('page')
        paged_product = paginator.get_page(page)
        product_count = products.count()
    else:
        products = Product.objects.all().filter(is_available=True).order_by('id')
        paginator = Paginator(products, 2)
        page = request.GET.get('page')
        paged_product = paginator.get_page(page)
        product_count = products.count()
    content = {
        'products': paged_product,
        'product_count': product_count,

    }
    return render(request, 'store/store.html', content)


def product_detail(request, category_slug, product_slug):
    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=session(request), product=single_product).exists()
        # cart = Cart.objects.get(cart_id=_session(request))
        # cart_item = get_object_or_404(CartItem, product=single_product, cart=cart)

    except Exception as e:
        raise e
    if request.user.is_authenticated:    
        try:
            orderproduct = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()

        except OrderProduct.DoesNotExist:
            orderproduct = None
    else:
        orderproduct = None
    #get all reviews 
    reviews = ReviewRating.objects.filter(product_id = single_product.id, status=True)
    context = {
        'single_product': single_product,
        'in_cart': in_cart,
        'orderproduct': orderproduct,
        'reviews': reviews,
    }
    return render(request, 'store/product_detail.html', context)


def search(request):
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            # aşagıdaki satıra filter kısmında Q objesini kompleks queryler için kullanıyoruz.
            products = Product.objects.order_by('-created_date').filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
            product_count = products.count()
    context = {
        'products': products,
        'product_count': product_count,

    }
    return render(request, 'store/store.html', context)


def submit_review(request, product_id):
    print("submit review")
    #TODO: HTTP_REFERER kullanimi
    url = request.META.get("HTTP_REFERER")
    if request.method == "POST":
        
        #TODO:foreignkey i bulunan nesnelere ulasmak
   
        try:
            print(22)
            reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id) 
            print("user id degeri : ", request.user.id)
            #TODO:instance kullanmamiz nedeni eger bir review nesnesi var ise yeni olusturma update et     
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, "Thank you!Your review has been updated.")
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data["subject"]
                data.rating = form.cleaned_data["rating"]
                data.review = form.cleaned_data["review"]
                data.ip =  request.META.get("REMOTE_ADDR")
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, "Thank you!Your review has been saved")
                return redirect(url)            

def deneme(request):
    return HttpResponse("OK")