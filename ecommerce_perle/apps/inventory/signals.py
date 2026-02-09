from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.catalog.models import ProductVariant
from .models import StockLevel


@receiver(post_save, sender=ProductVariant)
def ensure_stock_level(sender, instance, created, **kwargs):
    if created:
        StockLevel.objects.get_or_create(variant=instance)
