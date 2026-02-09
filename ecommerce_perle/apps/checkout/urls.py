from django.urls import path
from .views import CheckoutConfirmApiView, checkout_page, whatsapp_checkout

urlpatterns = [
    path('', checkout_page, name='checkout-page'),
    path('whatsapp/', whatsapp_checkout, name='checkout-whatsapp'),
    path('api/checkout/confirm/', CheckoutConfirmApiView.as_view(), name='api-checkout-confirm'),
]
