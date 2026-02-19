from django.db import models
from apps.catalog.models import ProductVariant


class InventoryMovement(models.Model):
    IN = 'IN'
    OUT = 'OUT'
    ADJUST = 'ADJUST'
    MOVEMENT_TYPES = [(IN, 'Ingreso'), (OUT, 'Salida'), (ADJUST, 'Ajuste')]

    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, related_name='movements')
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()
    reason = models.CharField(max_length=180)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Movimiento de inventario'
        verbose_name_plural = 'Movimientos de inventario'
        indexes = [models.Index(fields=['variant', 'created_at'])]


class StockLevel(models.Model):
    variant = models.OneToOneField(ProductVariant, on_delete=models.CASCADE, related_name='stock_level')
    available = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Nivel de stock'
        verbose_name_plural = 'Niveles de stock'
        indexes = [models.Index(fields=['available'])]
