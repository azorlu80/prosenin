from .models import Category


# setting dosyasında templates altında context processors kısmına eklenir.bu sayede budaraki sorguyu istediğinimiz template de kullanabiliriz.

def menu_links(request):
    links = Category.objects.all()
    return dict(links=links)
