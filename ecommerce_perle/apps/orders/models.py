import uuid
from django.db import models
from apps.catalog.models import ProductVariant
from apps.customers.models import Address, Customer


class Cart(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=50, db_index=True, blank=True)
    currency = models.CharField(max_length=3, default='COP')
    created_at = models.DateTimeField(auto_now_add=True)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'variant')


class Coupon(models.Model):
    code = models.CharField(max_length=40, unique=True)
    percentage = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)


class Order(models.Model):
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    PAID = 'paid'
    CANCELLED = 'cancelled'
    STATUS_CHOICES = [(PENDING, 'Pendiente'), (CONFIRMED, 'Confirmado'), (PAID, 'Pagado'), (CANCELLED, 'Cancelado')]
    PAYMENT_CHOICES = [
        ('whatsapp', 'WhatsApp'),
        ('manual', 'Manual'),
        ('wompi', 'Wompi'),
        ('stripe', 'Stripe'),
    ]

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    session_key = models.CharField(max_length=50, blank=True, db_index=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    address = models.ForeignKey(Address, on_delete=models.PROTECT)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING, db_index=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='whatsapp')
    whatsapp_message = models.TextField(blank=True)
    subtotal = models.PositiveIntegerField(default=0)
    discount_total = models.PositiveIntegerField(default=0)
    grand_total = models.PositiveIntegerField(default=0)
    currency = models.CharField(max_length=3, default='COP')
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [models.Index(fields=['status', 'created_at'])]


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.PositiveIntegerField()
    line_total = models.PositiveIntegerField()


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20)
    changed_at = models.DateTimeField(auto_now_add=True)
