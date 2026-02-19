from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.admin import helpers
from django.db import transaction
from django.template.response import TemplateResponse

from .models import InventoryMovement, StockLevel


class StockAdjustForm(forms.Form):
    delta = forms.IntegerField(
        label='Ajuste de unidades',
        help_text='Valor positivo suma stock, valor negativo resta stock.',
    )
    reason = forms.CharField(max_length=180, label='Motivo')


@admin.register(StockLevel)
class StockLevelAdmin(admin.ModelAdmin):
    list_display = ('variant', 'available', 'is_low_stock', 'updated_at')
    list_filter = ('updated_at',)
    search_fields = ('variant__sku', 'variant__product__name')
    actions = ('adjust_stock',)

    @admin.display(boolean=True, description='Stock bajo')
    def is_low_stock(self, obj):
        return obj.available <= settings.LOW_STOCK_THRESHOLD

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

        context = {
            **self.admin_site.each_context(request),
            'title': 'Confirmar ajuste de stock',
            'stocks': queryset,
            'form': form,
            'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        }
        return TemplateResponse(request, 'admin/inventory/stocklevel/adjust_stock_confirmation.html', context)


@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = ('variant', 'movement_type', 'quantity', 'reason', 'created_at')
    list_filter = ('movement_type', 'created_at')
    search_fields = ('variant__sku', 'variant__product__name', 'reason')
