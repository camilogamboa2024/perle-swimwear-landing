from django.conf import settings
from django.db import DatabaseError, OperationalError, transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.customers.models import Address, Customer
from apps.orders.models import Coupon
from apps.orders.views import _get_or_create_cart
from core.authentication import EnforcedCsrfSessionAuthentication
from .serializers import CheckoutConfirmSerializer
from .services import CheckoutError, create_order_from_cart
from .whatsapp import build_whatsapp_url

CHECKOUT_BUSY_MESSAGE = 'El checkout está ocupado. Intenta nuevamente.'


@ensure_csrf_cookie
def checkout_page(request):
    return render(request, 'checkout/checkout.html')


def _is_concurrency_error(exc):
    if isinstance(exc, OperationalError):
        return True
    message = str(exc).lower()
    return any(
        token in message
        for token in (
            'locked',
            'deadlock',
            'could not obtain lock',
            'serialization failure',
            'timeout',
        )
    )


class CheckoutConfirmApiView(APIView):
    authentication_classes = [EnforcedCsrfSessionAuthentication]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'checkout'

    def post(self, request):
        serializer = CheckoutConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        cart = _get_or_create_cart(request)
        coupon = None
        coupon_code = (data.get('coupon_code') or '').strip()
        if coupon_code:
            coupon = Coupon.objects.filter(code__iexact=coupon_code).first()
            if not coupon or not coupon.is_valid_for_checkout(now=timezone.now()):
                return Response(
                    {'error': 'Cupón inválido o expirado.', 'code': 'invalid_coupon'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            with transaction.atomic():
                customer, _ = Customer.objects.get_or_create(
                    email=data['email'],
                    defaults={'full_name': data['full_name'], 'phone': data.get('phone', '')},
                )
                customer.full_name = data['full_name']
                customer.phone = data.get('phone', '')
                customer.save(update_fields=['full_name', 'phone'])
                address = Address.objects.create(
                    customer=customer,
                    line1=data['line1'],
                    city=data['city'],
                    state=data['state'],
                    country='Colombia',
                    label='Checkout',
                )
                order = create_order_from_cart(
                    customer=customer,
                    address=address,
                    cart=cart,
                    coupon=coupon,
                    payment_method=data['payment_method'],
                    session_key=request.session.session_key or '',
                )
        except CheckoutError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except (OperationalError, DatabaseError) as exc:
            if _is_concurrency_error(exc):
                return Response(
                    {'error': CHECKOUT_BUSY_MESSAGE, 'code': 'checkout_busy'},
                    status=status.HTTP_409_CONFLICT,
                )
            raise

        whatsapp_url = build_whatsapp_url(order.whatsapp_message, settings.WHATSAPP_PHONE) if settings.WHATSAPP_PHONE else ''
        return Response(
            {
                'order_id': order.id,
                'order_public_id': str(order.public_id),
                'whatsapp_url': whatsapp_url,
                'confirmation_url': reverse('order-confirmation', kwargs={'public_id': order.public_id}),
            },
            status=status.HTTP_201_CREATED,
        )


def whatsapp_checkout(request):
    return redirect('/')
