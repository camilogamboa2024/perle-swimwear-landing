from django.contrib import admin

from .models import Cart, CartItem, Coupon, Order, OrderItem, OrderStatusHistory


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'status', 'grand_total', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('id', 'customer__email')
    readonly_fields = ('subtotal', 'discount_total', 'grand_total', 'created_at')


admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(OrderItem)
admin.site.register(OrderStatusHistory)
admin.site.register(Coupon)
