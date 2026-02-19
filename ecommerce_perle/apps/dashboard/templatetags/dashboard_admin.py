from datetime import timedelta

from django import template
from django.conf import settings
from django.db.models import Sum
from django.utils import timezone

from apps.inventory.models import StockLevel
from apps.orders.models import Order

register = template.Library()


@register.simple_tag
def admin_kpis():
    now = timezone.localtime()
    today = now.date()
    week_start = today - timedelta(days=today.weekday())
    billable_statuses = [Order.CONFIRMED, Order.PAID, Order.SHIPPED, Order.DELIVERED]

    return {
        'orders_today': Order.objects.filter(created_at__date=today).count(),
        'orders_week': Order.objects.filter(created_at__date__gte=week_start).count(),
        'pending_orders': Order.objects.filter(status=Order.PENDING).count(),
        'low_stock_count': StockLevel.objects.filter(available__lte=settings.LOW_STOCK_THRESHOLD).count(),
        'revenue_week': (
            Order.objects.filter(created_at__date__gte=week_start, status__in=billable_statuses).aggregate(
                total=Sum('grand_total')
            )['total']
            or 0
        ),
    }
