from django.contrib import admin
from django.contrib.admin import helpers
from django.db import transaction
from django.template.response import TemplateResponse
from django.utils import timezone

from .models import Cart, CartItem, Coupon, Order, OrderItem, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = ('variant', 'quantity', 'unit_price', 'line_total')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('public_id', 'customer', 'customer_email', 'status', 'grand_total', 'payment_method', 'created_at')
    list_filter = ('status', 'created_at', 'payment_method')
    search_fields = ('public_id', 'customer__email')
    readonly_fields = (
        'public_id',
        'session_key',
        'customer',
        'address',
        'coupon',
        'payment_method',
        'subtotal',
        'discount_total',
        'grand_total',
        'created_at',
        'whatsapp_message',
        'paid_at',
    )
    inlines = [OrderItemInline]
    actions = ('mark_paid', 'mark_shipped', 'mark_delivered', 'mark_cancelled')

    @admin.display(ordering='customer__email', description='Email')
    def customer_email(self, obj):
        return obj.customer.email

    def _transition_orders(self, request, queryset, to_status):
        updated = 0
        now = timezone.now()
        with transaction.atomic():
            for order in queryset.select_for_update():
                from_status = order.status
                if from_status == to_status:
                    continue
                order.status = to_status
                update_fields = ['status']
                if to_status == Order.PAID and not order.paid_at:
                    order.paid_at = now
                    update_fields.append('paid_at')
                order.save(update_fields=update_fields)
                OrderStatusHistory.objects.create(
                    order=order,
                    from_status=from_status,
                    to_status=to_status,
                )
                updated += 1
        if updated:
            self.message_user(request, f'Se actualizaron {updated} órdenes.')
        else:
            self.message_user(request, 'No hubo cambios para aplicar.')
        return None

    def _confirm_action(self, request, queryset, title, action_name):
        context = {
            **self.admin_site.each_context(request),
            'title': title,
            'orders': queryset,
            'action_name': action_name,
            'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        }
        return TemplateResponse(request, 'admin/orders/order/action_confirmation.html', context)

    def _run_action(self, request, queryset, *, to_status, title, action_name):
        if request.POST.get('apply'):
            return self._transition_orders(request, queryset, to_status)
        return self._confirm_action(request, queryset, title, action_name)

    @admin.action(description='Marcar como pagadas')
    def mark_paid(self, request, queryset):
        return self._run_action(
            request,
            queryset,
            to_status=Order.PAID,
            title='Confirmar cambio a estado "Pagado"',
            action_name='mark_paid',
        )

    @admin.action(description='Marcar como enviadas')
    def mark_shipped(self, request, queryset):
        return self._run_action(
            request,
            queryset,
            to_status=Order.SHIPPED,
            title='Confirmar cambio a estado "Enviado"',
            action_name='mark_shipped',
        )

    @admin.action(description='Marcar como entregadas')
    def mark_delivered(self, request, queryset):
        return self._run_action(
            request,
            queryset,
            to_status=Order.DELIVERED,
            title='Confirmar cambio a estado "Entregado"',
            action_name='mark_delivered',
        )

    @admin.action(description='Marcar como canceladas')
    def mark_cancelled(self, request, queryset):
        return self._run_action(
            request,
            queryset,
            to_status=Order.CANCELLED,
            title='Confirmar cambio a estado "Cancelado"',
            action_name='mark_cancelled',
        )


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'percentage', 'is_active', 'expires_at')
    list_filter = ('is_active', 'expires_at')
    search_fields = ('code',)
    actions = ('activate_coupons', 'deactivate_coupons')

    @admin.action(description='Activar cupones')
    def activate_coupons(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'Se activaron {updated} cupones.')

    @admin.action(description='Desactivar cupones')
    def deactivate_coupons(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'Se desactivaron {updated} cupones.')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'session_key', 'currency', 'created_at')
    search_fields = ('session_key', 'customer__email')
    list_filter = ('created_at',)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'variant', 'quantity')
    search_fields = ('variant__sku', 'cart__customer__email', 'cart__session_key')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'variant', 'quantity', 'unit_price', 'line_total')
    search_fields = ('variant__sku', 'order__public_id')
    list_filter = ('order__created_at',)


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('order', 'from_status', 'to_status', 'changed_at')
    list_filter = ('to_status', 'changed_at')
    search_fields = ('order__public_id',)
