from datetime import timedelta

from django import template
from django.conf import settings
from django.db.models import Count, Sum
from django.utils import timezone

from apps.inventory.models import StockLevel
from apps.orders.models import Order, OrderItem

register = template.Library()


def _format_delta(current, previous):
    if previous <= 0:
        if current <= 0:
            return 0
        return 100
    return int(((current - previous) / previous) * 100)


def _line_series(*, today, days, billable_statuses):
    start = today - timedelta(days=days - 1)
    dates = [start + timedelta(days=index) for index in range(days)]
    orders_map = {day: 0 for day in dates}
    revenue_map = {day: 0 for day in dates}

    orders_rows = (
        Order.objects.filter(created_at__date__gte=start)
        .values('created_at__date')
        .annotate(total=Count('id'))
    )
    for row in orders_rows:
        row_date = row['created_at__date']
        if row_date in orders_map:
            orders_map[row_date] = row['total'] or 0

    revenue_rows = (
        Order.objects.filter(created_at__date__gte=start, status__in=billable_statuses)
        .values('created_at__date')
        .annotate(total=Sum('grand_total'))
    )
    for row in revenue_rows:
        row_date = row['created_at__date']
        if row_date in revenue_map:
            revenue_map[row_date] = row['total'] or 0

    labels = [day.strftime('%d/%m') for day in dates]
    return {
        'labels': labels,
        'orders': [orders_map[day] for day in dates],
        'revenue': [revenue_map[day] for day in dates],
    }


@register.simple_tag
def admin_kpis():
    now = timezone.localtime()
    today = now.date()
    yesterday = today - timedelta(days=1)
    week_start = today - timedelta(days=today.weekday())
    previous_week_start = week_start - timedelta(days=7)
    previous_week_end = week_start - timedelta(days=1)
    billable_statuses = [Order.CONFIRMED, Order.PAID, Order.SHIPPED, Order.DELIVERED]

    orders_today = Order.objects.filter(created_at__date=today).count()
    orders_yesterday = Order.objects.filter(created_at__date=yesterday).count()
    orders_week = Order.objects.filter(created_at__date__gte=week_start).count()
    orders_previous_week = Order.objects.filter(
        created_at__date__gte=previous_week_start,
        created_at__date__lte=previous_week_end,
    ).count()
    pending_orders = Order.objects.filter(status=Order.PENDING).count()
    low_stock_count = StockLevel.objects.filter(available__lte=settings.LOW_STOCK_THRESHOLD).count()
    revenue_week = (
        Order.objects.filter(created_at__date__gte=week_start, status__in=billable_statuses).aggregate(
            total=Sum('grand_total')
        )['total']
        or 0
    )
    revenue_previous_week = (
        Order.objects.filter(
            created_at__date__gte=previous_week_start,
            created_at__date__lte=previous_week_end,
            status__in=billable_statuses,
        ).aggregate(total=Sum('grand_total'))['total']
        or 0
    )
    billable_orders_week = (
        Order.objects.filter(created_at__date__gte=week_start, status__in=billable_statuses).count()
    )
    ticket_avg_week = int(revenue_week / billable_orders_week) if billable_orders_week else 0

    status_rows = (
        Order.objects.values('status')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    status_labels = dict(Order.STATUS_CHOICES)
    status_distribution = [
        {'label': status_labels.get(row['status'], row['status']), 'value': row['total']}
        for row in status_rows
    ]

    pending_recent = list(
        Order.objects.filter(status=Order.PENDING)
        .select_related('customer')
        .order_by('-created_at')[:6]
    )
    low_stock_items = list(
        StockLevel.objects.filter(available__lte=settings.LOW_STOCK_THRESHOLD)
        .select_related('variant__product')
        .order_by('available', '-updated_at')[:6]
    )
    top_products = list(
        OrderItem.objects.values('variant__product__name')
        .annotate(units=Sum('quantity'), revenue=Sum('line_total'))
        .order_by('-units')[:6]
    )

    return {
        'generated_at': now,
        'orders_today': orders_today,
        'orders_yesterday': orders_yesterday,
        'orders_today_delta': _format_delta(orders_today, orders_yesterday),
        'orders_week': orders_week,
        'orders_previous_week': orders_previous_week,
        'orders_week_delta': _format_delta(orders_week, orders_previous_week),
        'pending_orders': pending_orders,
        'low_stock_count': low_stock_count,
        'revenue_week': revenue_week,
        'revenue_previous_week': revenue_previous_week,
        'revenue_week_delta': _format_delta(revenue_week, revenue_previous_week),
        'ticket_avg_week': ticket_avg_week,
        'series_7d': _line_series(today=today, days=7, billable_statuses=billable_statuses),
        'series_30d': _line_series(today=today, days=30, billable_statuses=billable_statuses),
        'status_distribution': status_distribution,
        'pending_recent': pending_recent,
        'low_stock_items': low_stock_items,
        'top_products': top_products,
    }
