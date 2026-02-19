from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.admin import helpers
from django.db import transaction
from django.template.response import TemplateResponse
from django.utils.html import format_html

from .models import InventoryMovement, StockLevel


class StockAdjustForm(forms.Form):
    delta = forms.IntegerField(
        label='Ajuste de unidades',
        help_text='Valor positivo suma stock, valor negativo resta stock.',
    )
    reason = forms.CharField(max_length=180, label='Motivo')


class StockLevelAlertFilter(admin.SimpleListFilter):
    title = 'Alerta de stock'
    parameter_name = 'stock_alert'

    def lookups(self, request, model_admin):
        return (
            ('critical', 'Crítico (0)'),
            ('low', 'Bajo (<= umbral)'),
            ('healthy', 'Saludable (> umbral)'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'critical':
            return queryset.filter(available__lte=0)
        if value == 'low':
            return queryset.filter(available__gt=0, available__lte=settings.LOW_STOCK_THRESHOLD)
        if value == 'healthy':
            return queryset.filter(available__gt=settings.LOW_STOCK_THRESHOLD)
        return queryset


@admin.register(StockLevel)
class StockLevelAdmin(admin.ModelAdmin):
    list_display = (
        'product_name',
        'variant_sku',
        'available',
        'stock_alert_badge',
        'updated_at',
    )
    list_filter = (StockLevelAlertFilter, 'updated_at')
    search_fields = ('variant__sku', 'variant__product__name')
    actions = ('adjust_stock',)
    list_select_related = ('variant', 'variant__product')

    @admin.display(ordering='variant__product__name', description='Producto')
    def product_name(self, obj):
        return obj.variant.product.name

    @admin.display(ordering='variant__sku', description='SKU')
    def variant_sku(self, obj):
        return obj.variant.sku

    @admin.display(boolean=True, description='Stock bajo')
    def is_low_stock(self, obj):
        return obj.available <= settings.LOW_STOCK_THRESHOLD

    @admin.display(description='Alerta')
    def stock_alert_badge(self, obj):
        if obj.available <= 0:
            return format_html('<span class="perle-pill perle-pill-danger">Crítico</span>')
        if obj.available <= settings.LOW_STOCK_THRESHOLD:
            return format_html('<span class="perle-pill perle-pill-warning">Bajo</span>')
        return format_html('<span class="perle-pill perle-pill-success">Saludable</span>')

    @admin.action(description='Ajustar stock (con movimiento)')
    def adjust_stock(self, request, queryset):
        if request.POST.get('apply'):
            form = StockAdjustForm(request.POST)
            if form.is_valid():
                delta = form.cleaned_data['delta']
                reason = form.cleaned_data['reason']
                adjusted = 0
                with transaction.atomic():
                    for stock in queryset.select_for_update().select_related('variant'):
                        previous_available = stock.available
                        stock.available = max(previous_available + delta, 0)
                        applied_delta = stock.available - previous_available
                        stock.save(update_fields=['available', 'updated_at'])
                        InventoryMovement.objects.create(
                            variant=stock.variant,
                            movement_type=InventoryMovement.ADJUST,
                            quantity=applied_delta,
                            reason=reason,
                        )
                        adjusted += 1
                self.message_user(request, f'Se ajustó inventario en {adjusted} variantes.')
                return None
        else:
            form = StockAdjustForm()

        preview_delta = 0
        if form.is_bound and form.is_valid():
            preview_delta = form.cleaned_data['delta']

        selected_rows = list(queryset.select_related('variant', 'variant__product'))
        preview_rows = [
            {
                'stock': stock,
                'projected': max(stock.available + preview_delta, 0),
            }
            for stock in selected_rows
        ]

        context = {
            **self.admin_site.each_context(request),
            'title': 'Confirmar ajuste de stock',
            'stocks': selected_rows,
            'preview_rows': preview_rows,
            'preview_delta': preview_delta,
            'LOW_STOCK_THRESHOLD': settings.LOW_STOCK_THRESHOLD,
            'form': form,
            'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        }
        return TemplateResponse(request, 'admin/inventory/stocklevel/adjust_stock_confirmation.html', context)


@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = ('variant', 'movement_type', 'quantity', 'reason', 'created_at')
    list_filter = ('movement_type', 'created_at')
    search_fields = ('variant__sku', 'variant__product__name', 'reason')
