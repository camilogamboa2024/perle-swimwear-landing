from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError, IntegrityError, OperationalError, transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import ensure_csrf_cookie
from uuid import uuid4
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.customers.models import Customer
from apps.checkout.whatsapp import build_whatsapp_url
from apps.inventory.models import StockLevel
from core.authentication import EnforcedCsrfSessionAuthentication
from .models import Cart, CartItem, Order
from .serializers import AddCartItemSerializer, CartSerializer, UpdateCartItemSerializer

CART_BUSY_MESSAGE = 'El carrito está ocupado. Intenta nuevamente.'


def _unique_fallback_customer_email(user_id):
    base_email = f'user-{user_id}@local.test'
    if not Customer.objects.filter(email=base_email).exists():
        return base_email
    return f'user-{user_id}-{uuid4().hex[:8]}@local.test'


def _get_or_create_customer_for_user(user):
    preferred_email = (user.email or '').strip().lower()
    full_name = user.get_full_name() or user.username or f'user-{user.id}'

    customer = Customer.objects.filter(user=user).first()
    if customer:
        update_fields = []
        if full_name and customer.full_name != full_name:
            customer.full_name = full_name
            update_fields.append('full_name')
        if preferred_email and customer.email != preferred_email:
            email_taken = Customer.objects.exclude(pk=customer.pk).filter(email=preferred_email).exists()
            if not email_taken:
                customer.email = preferred_email
                update_fields.append('email')
        if update_fields:
            customer.save(update_fields=update_fields)
        return customer

    if preferred_email:
        existing_by_email = Customer.objects.filter(email=preferred_email).first()
        if existing_by_email and existing_by_email.user_id in (None, user.id):
            update_fields = []
            if existing_by_email.user_id != user.id:
                existing_by_email.user = user
                update_fields.append('user')
            if full_name and existing_by_email.full_name != full_name:
                existing_by_email.full_name = full_name
                update_fields.append('full_name')
            if update_fields:
                existing_by_email.save(update_fields=update_fields)
            return existing_by_email

    email_for_new_customer = preferred_email or _unique_fallback_customer_email(user.id)
    if Customer.objects.filter(email=email_for_new_customer).exists():
        email_for_new_customer = _unique_fallback_customer_email(user.id)
    return Customer.objects.create(
        user=user,
        email=email_for_new_customer,
        full_name=full_name,
    )


def _get_or_create_cart(request):
    return _get_or_create_cart_with_locking(request, for_update=False)


def _get_or_create_cart_with_locking(request, *, for_update=False):
    if request.user.is_authenticated:
        customer = _get_or_create_customer_for_user(request.user)
        lookup = {'customer': customer}
    else:
        if not request.session.session_key:
            request.session.create()
        lookup = {'session_key': request.session.session_key}

    with transaction.atomic():
        queryset = Cart.objects.select_for_update() if for_update else Cart.objects
        cart = queryset.filter(**lookup).first()
        if cart:
            return cart

    try:
        with transaction.atomic():
            cart = Cart.objects.create(currency='COP', **lookup)
            if for_update:
                return Cart.objects.select_for_update().get(pk=cart.pk)
            return cart
    except IntegrityError:
        with transaction.atomic():
            queryset = Cart.objects.select_for_update() if for_update else Cart.objects
            return queryset.get(**lookup)


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


def _cart_busy_response():
    return Response(
        {'error': CART_BUSY_MESSAGE, 'code': 'cart_busy'},
        status=status.HTTP_409_CONFLICT,
    )


def _validate_stock_for_quantity(variant, quantity, *, available=None):
    if not variant.is_active:
        return f'La variante {variant.sku} no está disponible.'
    stock_available = available
    if stock_available is None:
        try:
            stock_available = variant.stock_level.available
        except ObjectDoesNotExist:
            return f'Sin stock configurado para SKU {variant.sku}.'
    if quantity > stock_available:
        return f'Stock insuficiente para SKU {variant.sku}. Disponible: {stock_available}.'
    return ''


class CartApiView(APIView):
    def get(self, request):
        cart = _get_or_create_cart(request)
        return Response(CartSerializer(cart).data)


class CartItemsApiView(APIView):
    authentication_classes = [EnforcedCsrfSessionAuthentication]

    def post(self, request):
        serializer = AddCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        variant = serializer.validated_data['variant']
        quantity = serializer.validated_data['quantity']
        try:
            with transaction.atomic():
                cart = _get_or_create_cart_with_locking(request, for_update=True)
                item = CartItem.objects.select_for_update().filter(cart=cart, variant=variant).first()
                target_quantity = quantity if item is None else item.quantity + quantity

                try:
                    stock_available = StockLevel.objects.select_for_update().get(variant=variant).available
                except StockLevel.DoesNotExist:
                    return Response(
                        {'error': f'Sin stock configurado para SKU {variant.sku}.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                stock_error = _validate_stock_for_quantity(
                    variant,
                    target_quantity,
                    available=stock_available,
                )
                if stock_error:
                    return Response({'error': stock_error}, status=status.HTTP_400_BAD_REQUEST)

                if item is None:
                    CartItem.objects.create(cart=cart, variant=variant, quantity=quantity)
                else:
                    item.quantity = target_quantity
                    item.save(update_fields=['quantity'])
                payload = CartSerializer(cart).data
            return Response(payload, status=status.HTTP_201_CREATED)
        except (OperationalError, DatabaseError) as exc:
            if _is_concurrency_error(exc):
                return _cart_busy_response()
            raise


class CartItemDetailApiView(APIView):
    authentication_classes = [EnforcedCsrfSessionAuthentication]

    def patch(self, request, item_id):
        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_quantity = serializer.validated_data['quantity']
        try:
            with transaction.atomic():
                cart = _get_or_create_cart_with_locking(request, for_update=True)
                item = get_object_or_404(CartItem.objects.select_for_update(), id=item_id, cart=cart)

                try:
                    stock_available = StockLevel.objects.select_for_update().get(variant=item.variant).available
                except StockLevel.DoesNotExist:
                    return Response(
                        {'error': f'Sin stock configurado para SKU {item.variant.sku}.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                stock_error = _validate_stock_for_quantity(
                    item.variant,
                    new_quantity,
                    available=stock_available,
                )
                if stock_error:
                    return Response({'error': stock_error}, status=status.HTTP_400_BAD_REQUEST)

                item.quantity = new_quantity
                item.save(update_fields=['quantity'])
                payload = CartSerializer(cart).data
            return Response(payload)
        except (OperationalError, DatabaseError) as exc:
            if _is_concurrency_error(exc):
                return _cart_busy_response()
            raise

    def delete(self, request, item_id):
        try:
            with transaction.atomic():
                cart = _get_or_create_cart_with_locking(request, for_update=True)
                item = get_object_or_404(CartItem.objects.select_for_update(), id=item_id, cart=cart)
                item.delete()
                payload = CartSerializer(cart).data
            return Response(payload)
        except (OperationalError, DatabaseError) as exc:
            if _is_concurrency_error(exc):
                return _cart_busy_response()
            raise


class CartClearApiView(APIView):
    authentication_classes = [EnforcedCsrfSessionAuthentication]

    def post(self, request):
        try:
            with transaction.atomic():
                cart = _get_or_create_cart_with_locking(request, for_update=True)
                CartItem.objects.select_for_update().filter(cart=cart).delete()
                payload = CartSerializer(cart).data
            return Response(payload)
        except (OperationalError, DatabaseError) as exc:
            if _is_concurrency_error(exc):
                return _cart_busy_response()
            raise


@ensure_csrf_cookie
def cart_page(request):
    cart = _get_or_create_cart(request)
    return render(request, 'orders/cart.html', {'cart': cart, 'totals': CartSerializer(cart).data['totals']})


@ensure_csrf_cookie
def order_confirmation(request, public_id):
    order = get_object_or_404(Order.objects.prefetch_related('items__variant__product'), public_id=public_id)
    if order.session_key and request.session.session_key != order.session_key:
        raise Http404('Pedido no encontrado')
    whatsapp_url = build_whatsapp_url(order.whatsapp_message, settings.WHATSAPP_PHONE) if settings.WHATSAPP_PHONE else ''
    return render(request, 'orders/confirmation.html', {'order': order, 'whatsapp_url': whatsapp_url})
