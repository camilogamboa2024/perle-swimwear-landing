from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.customers.models import Customer
from apps.checkout.whatsapp import build_whatsapp_url
from .models import Cart, CartItem, Order
from .serializers import AddCartItemSerializer, CartSerializer, UpdateCartItemSerializer


def _get_or_create_cart(request):
    if request.user.is_authenticated:
        customer, _ = Customer.objects.get_or_create(
            user=request.user,
            defaults={
                'email': request.user.email or f'user-{request.user.id}@local.test',
                'full_name': request.user.get_full_name() or request.user.username,
            },
        )
        cart, _ = Cart.objects.get_or_create(customer=customer, defaults={'currency': 'COP'})
        return cart

    if not request.session.session_key:
        request.session.create()
    cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key, defaults={'currency': 'COP'})
    return cart


class CartApiView(APIView):
    def get(self, request):
        cart = _get_or_create_cart(request)
        return Response(CartSerializer(cart).data)


class CartItemsApiView(APIView):
    def post(self, request):
        cart = _get_or_create_cart(request)
        serializer = AddCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        variant = serializer.validated_data['variant']
        quantity = serializer.validated_data['quantity']
        item, created = CartItem.objects.get_or_create(cart=cart, variant=variant, defaults={'quantity': quantity})
        if not created:
            item.quantity += quantity
            item.save(update_fields=['quantity'])
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)


class CartItemDetailApiView(APIView):
    def patch(self, request, item_id):
        cart = _get_or_create_cart(request)
        item = get_object_or_404(CartItem, id=item_id, cart=cart)
        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item.quantity = serializer.validated_data['quantity']
        item.save(update_fields=['quantity'])
        return Response(CartSerializer(cart).data)

    def delete(self, request, item_id):
        cart = _get_or_create_cart(request)
        item = get_object_or_404(CartItem, id=item_id, cart=cart)
        item.delete()
        return Response(CartSerializer(cart).data)


class CartClearApiView(APIView):
    def post(self, request):
        cart = _get_or_create_cart(request)
        cart.items.all().delete()
        return Response(CartSerializer(cart).data)


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
