from django.contrib import admin
from .models import Address, Customer

admin.site.register(Customer)
admin.site.register(Address)
