from django.contrib import admin

from .models import InventoryMovement, StockLevel


@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = ('variant', 'movement_type', 'quantity', 'reason', 'created_at')
    list_filter = ('movement_type', 'created_at')
    search_fields = ('variant__sku', 'reason')


admin.site.register(StockLevel)
