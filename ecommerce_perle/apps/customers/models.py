from django.conf import settings
from django.db import models


class Customer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'


class Address(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='addresses')
    label = models.CharField(max_length=50, default='Casa')
    line1 = models.CharField(max_length=180)
    line2 = models.CharField(max_length=180, blank=True)
    city = models.CharField(max_length=80)
    state = models.CharField(max_length=80)
    country = models.CharField(max_length=80, default='Panama')
    postal_code = models.CharField(max_length=20, blank=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Dirección'
        verbose_name_plural = 'Direcciones'
