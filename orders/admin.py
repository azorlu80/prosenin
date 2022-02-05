from django.contrib import admin
from .models import Order, Payment, OrderProduct



#TODO:admin panaelinde inline kullanimi
class OrderProduct_Inline(admin.TabularInline):
    model = OrderProduct
    readonly_fields = ("payment","user","product","quantity","product_price","ordered")
    extra = 0


class Payment_Admin(admin.ModelAdmin):
    list_per_page = 10
    list_display = ('user', 'payment_id', "payment_method", "amount_payment", "status", "created_at")

class Order_Admin(admin.ModelAdmin):
    list_per_page = 10
    list_display = ('order_number', 'user', "full_name","status", "order_total","order_note","is_ordered")
    list_filter = ("status", "is_ordered")
    search_fields = ("order_number", "email")
    inlines = [OrderProduct_Inline]

class OrderProduct_Admin(admin.ModelAdmin):
    list_per_page = 10
    list_display = ('order', "user", "product","quantity","product_price","ordered","payment")


admin.site.register(Order, Order_Admin)
admin.site.register(Payment, Payment_Admin)
admin.site.register(OrderProduct, OrderProduct_Admin)
