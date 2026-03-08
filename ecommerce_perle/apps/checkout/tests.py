from datetime import timedelta
import json
from unittest.mock import patch

from django.db import OperationalError
from django.test import Client, TestCase
from django.utils import timezone

from apps.catalog.models import Category, Product, ProductVariant
from apps.customers.models import Address, Customer
from apps.inventory.models import InventoryMovement, StockLevel
from apps.orders.models import Cart, CartItem, Coupon, Order
from .services import create_order_from_cart


class CheckoutServiceTest(TestCase):
    def setUp(self):
        category = Category.objects.create(name='Bikinis', slug='bikinis')
        product = Product.objects.create(name='Test', slug='test', category=category, description='x')
        self.variant = ProductVariant.objects.create(
            product=product, sku='SKU-1', size='S', color='Negro', price_usd_cents=100000
        )
        StockLevel.objects.update_or_create(variant=self.variant, defaults={'available': 5})
        self.customer = Customer.objects.create(email='test@example.com', full_name='Cliente')
        self.address = Address.objects.create(
            customer=self.customer,
            line1='Calle 1',
            city='Ciudad de Panamá',
            state='Panamá',
            country='Panama',
        )

    def test_stock_cannot_go_negative(self):
        cart = Cart.objects.create(customer=self.customer)
        CartItem.objects.create(cart=cart, variant=self.variant, quantity=10)
        with self.assertRaisesMessage(ValueError, 'Sin stock'):
            create_order_from_cart(customer=self.customer, address=self.address, cart=cart)

    def test_checkout_decreases_stock_and_calculates_total(self):
        cart = Cart.objects.create(customer=self.customer)
        CartItem.objects.create(cart=cart, variant=self.variant, quantity=2)
        order = create_order_from_cart(customer=self.customer, address=self.address, cart=cart)
        self.assertEqual(order.grand_total, 200000)
        self.variant.stock_level.refresh_from_db()
        self.assertEqual(self.variant.stock_level.available, 3)

    def test_coupon_applies_discount(self):
        cart = Cart.objects.create(customer=self.customer)
        CartItem.objects.create(cart=cart, variant=self.variant, quantity=2)
        coupon = Coupon.objects.create(code='PERLE10', percentage=10, is_active=True)
        order = create_order_from_cart(customer=self.customer, address=self.address, cart=cart, coupon=coupon)
        self.assertEqual(order.discount_total, 20000)
        self.assertEqual(order.grand_total, 180000)

    def test_empty_cart_raises_error(self):
        cart = Cart.objects.create(customer=self.customer)
        with self.assertRaisesMessage(ValueError, 'vacío'):
            create_order_from_cart(customer=self.customer, address=self.address, cart=cart)

    def test_inventory_movement_created(self):
        cart = Cart.objects.create(customer=self.customer)
        CartItem.objects.create(cart=cart, variant=self.variant, quantity=1)
        order = create_order_from_cart(customer=self.customer, address=self.address, cart=cart)
        self.assertTrue(InventoryMovement.objects.filter(reason=f'Order #{order.id}').exists())

    def test_missing_stock_level_raises_error(self):
        self.variant.stock_level.delete()
        cart = Cart.objects.create(customer=self.customer)
        CartItem.objects.create(cart=cart, variant=self.variant, quantity=1)
        with self.assertRaisesMessage(ValueError, 'Sin stock configurado'):
            create_order_from_cart(customer=self.customer, address=self.address, cart=cart)

    def test_total_never_negative_with_full_discount_coupon(self):
        cart = Cart.objects.create(customer=self.customer)
        CartItem.objects.create(cart=cart, variant=self.variant, quantity=1)
        coupon = Coupon.objects.create(code='FREE100', percentage=100, is_active=True)
        order = create_order_from_cart(customer=self.customer, address=self.address, cart=cart, coupon=coupon)
        self.assertEqual(order.discount_total, 100000)
        self.assertEqual(order.grand_total, 0)


class CheckoutConfirmApiViewTest(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        category = Category.objects.create(name='One Piece', slug='one-piece')
        product = Product.objects.create(name='Model', slug='model', category=category, description='x')
        self.variant = ProductVariant.objects.create(
            product=product, sku='SKU-API-1', size='M', color='Negro', price_usd_cents=150000
        )
        StockLevel.objects.update_or_create(variant=self.variant, defaults={'available': 1})

    def _csrf_headers(self, path='/'):
        response = self.client.get(path)
        token = response.cookies.get('csrftoken').value
        return {'HTTP_X_CSRFTOKEN': token}

    def _payload(self, email, coupon_code=''):
        return {
            'full_name': 'Cliente API',
            'email': email,
            'phone': '',
            'line1': 'Calle 123',
            'city': 'Ciudad de Panamá',
            'state': 'Panamá',
            'coupon_code': coupon_code,
            'payment_method': 'whatsapp',
        }

    def _add_to_cart(self, quantity):
        headers = self._csrf_headers('/')
        return self.client.post(
            '/api/cart/items/',
            data=json.dumps({'variant_id': self.variant.id, 'quantity': quantity}),
            content_type='application/json',
            **headers,
        )

    def _confirm_checkout(self, email, with_csrf=True, coupon_code=''):
        headers = self._csrf_headers('/checkout/') if with_csrf else {}
        return self.client.post(
            '/checkout/api/checkout/confirm/',
            data=json.dumps(self._payload(email, coupon_code=coupon_code)),
            content_type='application/json',
            **headers,
        )

    def test_empty_cart_returns_400_and_rolls_back_customer_data(self):
        response = self._confirm_checkout('empty-cart@example.com')
        self.assertEqual(response.status_code, 400)
        self.assertIn('vacío', response.json().get('error', '').lower())
        self.assertFalse(Customer.objects.filter(email='empty-cart@example.com').exists())
        self.assertFalse(Address.objects.exists())

    def test_out_of_stock_returns_400_and_rolls_back_customer_data(self):
        add_response = self._add_to_cart(quantity=1)
        self.assertEqual(add_response.status_code, 201)
        StockLevel.objects.filter(variant=self.variant).update(available=0)

        response = self._confirm_checkout('out-of-stock@example.com')
        self.assertEqual(response.status_code, 400)
        self.assertIn('sin stock', response.json().get('error', '').lower())
        self.assertFalse(Customer.objects.filter(email='out-of-stock@example.com').exists())
        self.assertFalse(Address.objects.exists())

    def test_missing_stock_level_returns_400(self):
        add_response = self._add_to_cart(quantity=1)
        self.assertEqual(add_response.status_code, 201)
        self.variant.stock_level.delete()

        response = self._confirm_checkout('missing-stock@example.com')
        self.assertEqual(response.status_code, 400)
        self.assertIn('stock configurado', response.json().get('error', '').lower())
        self.assertFalse(Customer.objects.filter(email='missing-stock@example.com').exists())
        self.assertFalse(Address.objects.exists())

    def test_checkout_confirm_requires_csrf_token(self):
        response = self._confirm_checkout('missing-csrf@example.com', with_csrf=False)
        self.assertEqual(response.status_code, 403)

    def test_double_submit_returns_400_on_second_attempt_and_keeps_single_order(self):
        add_response = self._add_to_cart(quantity=1)
        self.assertEqual(add_response.status_code, 201)

        first_response = self._confirm_checkout('double-submit@example.com')
        self.assertEqual(first_response.status_code, 201)

        second_response = self._confirm_checkout('double-submit@example.com')
        self.assertEqual(second_response.status_code, 400)
        self.assertIn('vacío', second_response.json().get('error', '').lower())
        self.assertEqual(Order.objects.filter(customer__email='double-submit@example.com').count(), 1)

    def test_invalid_coupon_returns_400_with_stable_error_code(self):
        add_response = self._add_to_cart(quantity=1)
        self.assertEqual(add_response.status_code, 201)

        response = self._confirm_checkout('invalid-coupon@example.com', coupon_code='NOEXISTE')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get('code'), 'invalid_coupon')
        self.assertIn('cupón inválido', response.json().get('error', '').lower())
        self.assertEqual(Order.objects.filter(customer__email='invalid-coupon@example.com').count(), 0)

    def test_expired_coupon_returns_400_with_stable_error_code(self):
        Coupon.objects.create(
            code='EXP10',
            percentage=10,
            is_active=True,
            expires_at=timezone.now() - timedelta(hours=1),
        )
        add_response = self._add_to_cart(quantity=1)
        self.assertEqual(add_response.status_code, 201)

        response = self._confirm_checkout('expired-coupon@example.com', coupon_code='EXP10')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get('code'), 'invalid_coupon')
        self.assertIn('cupón inválido', response.json().get('error', '').lower())

    def test_valid_coupon_applies_discount_on_checkout(self):
        Coupon.objects.create(
            code='PERLE15',
            percentage=15,
            is_active=True,
            expires_at=timezone.now() + timedelta(days=1),
        )
        add_response = self._add_to_cart(quantity=1)
        self.assertEqual(add_response.status_code, 201)

        response = self._confirm_checkout('valid-coupon@example.com', coupon_code='PERLE15')
        self.assertEqual(response.status_code, 201)
        order = Order.objects.get(customer__email='valid-coupon@example.com')
        self.assertEqual(order.discount_total, 22500)
        self.assertEqual(order.grand_total, 127500)
        self.assertEqual(order.address.country, 'Panama')

    def test_checkout_returns_409_when_db_is_busy(self):
        add_response = self._add_to_cart(quantity=1)
        self.assertEqual(add_response.status_code, 201)

        with patch(
            'apps.checkout.views.create_order_from_cart',
            side_effect=OperationalError('database is locked'),
        ):
            response = self._confirm_checkout('busy-checkout@example.com')

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json().get('code'), 'checkout_busy')
