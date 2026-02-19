from django.contrib import admin
from django.db.models import Max, Sum
from django.db.models.functions import Coalesce
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
    list_display = (
        'email',
        'full_name',
        'phone',
        'orders_count',
        'total_spent_cop',
        'last_order_at',
        'orders_link',
        'created_at',
    )
    search_fields = ('email', 'full_name', 'phone')
    readonly_fields = ('created_at', 'orders_link', 'total_spent_cop', 'last_order_at')
    list_filter = ('created_at',)
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

    @admin.display(ordering='total_spent', description='Total comprado')
    def total_spent_cop(self, obj):
        value = f'{obj.total_spent:,.0f}'.replace(',', '.')
        return f'${value} COP'

    @admin.display(ordering='last_order', description='Último pedido')
    def last_order_at(self, obj):
        if not obj.last_order:
            return 'Sin pedidos'
        return obj.last_order.strftime('%d/%m/%Y %H:%M')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            total_spent=Coalesce(Sum('order__grand_total'), 0),
            last_order=Max('order__created_at'),
        )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('customer', 'label', 'line1', 'city', 'state', 'is_default')
    list_filter = ('is_default', 'city', 'state')
    search_fields = ('customer__email', 'line1', 'city', 'state', 'postal_code')
