from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from apps.orders.models import Order
from .models import Address, Customer


class AddressInline(admin.TabularInline):
    model = Address
    extra = 0
    fields = ('label', 'line1', 'city', 'state', 'country', 'postal_code', 'is_default')


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('email', 'full_name', 'phone', 'orders_count', 'orders_link', 'created_at')
    search_fields = ('email', 'full_name', 'phone')
    readonly_fields = ('created_at', 'orders_link')
    inlines = [AddressInline]

    @admin.display(description='Pedidos')
    def orders_count(self, obj):
        return obj.order_set.count()

    @admin.display(description='Historial')
    def orders_link(self, obj):
        count = Order.objects.filter(customer=obj).count()
        if count == 0:
            return 'Sin pedidos'
        url = (
            reverse('admin:orders_order_changelist')
            + f'?customer__id__exact={obj.id}'
        )
        return format_html('<a href="{}">Ver {} pedido(s)</a>', url, count)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('customer', 'label', 'line1', 'city', 'state', 'is_default')
    list_filter = ('is_default', 'city', 'state')
    search_fields = ('customer__email', 'line1', 'city', 'state', 'postal_code')
