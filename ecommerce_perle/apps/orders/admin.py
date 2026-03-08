from datetime import timedelta

from django.contrib import admin
from django.contrib.admin import helpers
from django.db.models import Q
from django.db import transaction
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.utils import timezone

from apps.orders.money import format_usd

from .models import Cart, CartItem, Coupon, Order, OrderItem, OrderStatusHistory


class OrderPeriodFilter(admin.SimpleListFilter):
    title = 'Periodo rápido'
    parameter_name = 'periodo'

    def lookups(self, request, model_admin):
        return (
            ('hoy', 'Hoy'),
            ('semana', 'Esta semana'),
            ('pendientes', 'Solo pendientes'),
        )

    def queryset(self, request, queryset):
        today = timezone.localdate()
        value = self.value()
        if value == 'hoy':
            return queryset.filter(created_at__date=today)
        if value == 'semana':
            week_start = today - timedelta(days=today.weekday())
            return queryset.filter(created_at__date__gte=week_start)
        if value == 'pendientes':
            return queryset.filter(status=Order.PENDING)
        return queryset


class CouponValidityFilter(admin.SimpleListFilter):
    title = 'Vigencia'
    parameter_name = 'vigencia'

    def lookups(self, request, model_admin):
        return (
            ('vigente', 'Vigente'),
            ('expirado', 'Expirado'),
            ('por_vencer', 'Expira en 7 días'),
        )

    def queryset(self, request, queryset):
        now = timezone.now()
        value = self.value()
        if value == 'vigente':
            return queryset.filter(is_active=True).filter(coupon_valid_q(now))
        if value == 'expirado':
            return queryset.filter(expires_at__isnull=False, expires_at__lte=now)
        if value == 'por_vencer':
            return queryset.filter(expires_at__gt=now, expires_at__lte=now + timedelta(days=7))
        return queryset


def coupon_valid_q(now):
    return (
        Q(expires_at__isnull=True) | Q(expires_at__gt=now)
    )


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    fields = ('variant', 'quantity', 'unit_price_usd', 'line_total_usd')
    readonly_fields = ('variant', 'quantity', 'unit_price_usd', 'line_total_usd')

    @admin.display(description='Precio unitario')
    def unit_price_usd(self, obj):
        return format_usd(obj.unit_price)

    @admin.display(description='Total línea')
    def line_total_usd(self, obj):
        return format_usd(obj.line_total)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'public_id',
        'customer',
        'customer_email',
        'status_badge',
        'grand_total_usd',
        'payment_method',
        'created_at',
    )
    list_filter = ('status', OrderPeriodFilter, 'created_at', 'payment_method')
    search_fields = ('public_id', 'customer__email')
    list_select_related = ('customer', 'address', 'coupon')
    list_per_page = 25
    readonly_fields = (
        'public_id',
        'session_key',
        'customer_snapshot',
        'address_snapshot',
        'coupon',
        'payment_method',
        'subtotal_usd',
        'discount_total_usd',
        'grand_total_usd',
        'created_at',
        'whatsapp_message',
        'paid_at',
        'status_timeline',
    )
    inlines = [OrderItemInline]
    actions = ('mark_paid', 'mark_shipped', 'mark_delivered', 'mark_cancelled')
    fieldsets = (
        (
            'Resumen',
            {
                'fields': (
                    'public_id',
                    'status',
                    'payment_method',
                    'paid_at',
                    'created_at',
                )
            },
        ),
        (
            'Cliente y dirección',
            {
                'fields': (
                    'customer_snapshot',
                    'address_snapshot',
                )
            },
        ),
        (
            'Montos',
            {
                'fields': (
                    'subtotal_usd',
                    'discount_total_usd',
                    'grand_total_usd',
                    'coupon',
                )
            },
        ),
        (
            'Timeline',
            {
                'fields': (
                    'status_timeline',
                    'whatsapp_message',
                    'session_key',
                )
            },
        ),
    )

    @admin.display(ordering='customer__email', description='Email')
    def customer_email(self, obj):
        return obj.customer.email

    @admin.display(ordering='status', description='Estado')
    def status_badge(self, obj):
        badge_map = {
            Order.PENDING: 'warning',
            Order.CONFIRMED: 'info',
            Order.PAID: 'success',
            Order.SHIPPED: 'info',
            Order.DELIVERED: 'success',
            Order.CANCELLED: 'danger',
        }
        css_class = badge_map.get(obj.status, 'muted')
        return format_html(
            '<span class="perle-pill perle-pill-{}">{}</span>',
            css_class,
            obj.get_status_display(),
        )

    @admin.display(ordering='subtotal', description='Subtotal')
    def subtotal_usd(self, obj):
        return format_usd(obj.subtotal)

    @admin.display(ordering='discount_total', description='Descuento')
    def discount_total_usd(self, obj):
        return format_usd(obj.discount_total)

    @admin.display(ordering='grand_total', description='Total')
    def grand_total_usd(self, obj):
        return format_usd(obj.grand_total)

    @admin.display(description='Cliente')
    def customer_snapshot(self, obj):
        return format_html(
            '<strong>{}</strong><br><span>{}</span><br><small>{}</small>',
            obj.customer.full_name or 'Sin nombre',
            obj.customer.email,
            obj.customer.phone or 'Sin teléfono',
        )

    @admin.display(description='Dirección')
    def address_snapshot(self, obj):
        address = obj.address
        return format_html(
            '{}<br>{}, {}<br>{}',
            address.line1,
            address.city,
            address.state,
            address.country,
        )

    @admin.display(description='Timeline de estados')
    def status_timeline(self, obj):
        events = obj.status_history.order_by('-changed_at')[:10]
        if not events:
            return 'Sin historial registrado.'
        rows = []
        for event in events:
            rows.append(
                (
                    event.changed_at.strftime('%d/%m/%Y %H:%M'),
                    str(event.order.public_id),
                    event.from_status or 'N/A',
                    event.to_status,
                )
            )
        return format_html(
            '<ul class="perle-list">{}</ul>',
            format_html(
                ''.join(
                    [
                        (
                            '<li><strong>{}</strong> <small>({})</small>'
                            '<br><span>{} → {}</span></li>'
                        ).format(changed_at, public_id, from_status, to_status)
                        for changed_at, public_id, from_status, to_status in rows
                    ]
                )
            ),
        )

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

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('customer', 'address', 'coupon').prefetch_related('status_history')

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
    list_display = ('code', 'percentage', 'active_badge', 'validity_badge', 'expires_at')
    list_filter = ('is_active', CouponValidityFilter, 'expires_at')
    search_fields = ('code',)
    actions = ('activate_coupons', 'deactivate_coupons')

    @admin.display(description='Activo')
    def active_badge(self, obj):
        if obj.is_active:
            return format_html('<span class="perle-pill perle-pill-success">Activo</span>')
        return format_html('<span class="perle-pill perle-pill-danger">Inactivo</span>')

    @admin.display(description='Vigencia')
    def validity_badge(self, obj):
        now = timezone.now()
        if obj.expires_at and obj.expires_at <= now:
            return format_html('<span class="perle-pill perle-pill-danger">Expirado</span>')
        if obj.expires_at and obj.expires_at <= now + timedelta(days=7):
            return format_html('<span class="perle-pill perle-pill-warning">Por vencer</span>')
        return format_html('<span class="perle-pill perle-pill-success">Vigente</span>')

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
    list_display = ('order', 'variant', 'quantity', 'unit_price_usd', 'line_total_usd')
    search_fields = ('variant__sku', 'order__public_id')
    list_filter = ('order__created_at',)

    @admin.display(ordering='unit_price', description='Precio unitario')
    def unit_price_usd(self, obj):
        return format_usd(obj.unit_price)

    @admin.display(ordering='line_total', description='Total línea')
    def line_total_usd(self, obj):
        return format_usd(obj.line_total)


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('order', 'from_status', 'to_status', 'changed_at')
    list_filter = ('to_status', 'changed_at')
    search_fields = ('order__public_id',)
