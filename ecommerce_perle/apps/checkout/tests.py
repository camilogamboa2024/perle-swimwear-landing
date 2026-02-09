from django.test import TestCase

from apps.catalog.models import Category, Product, ProductVariant
from apps.customers.models import Address, Customer
from apps.inventory.models import InventoryMovement, StockLevel
from apps.orders.models import Cart, CartItem, Coupon
from .services import create_order_from_cart


class CheckoutServiceTest(TestCase):
    def setUp(self):
        category = Category.objects.create(name='Bikinis', slug='bikinis')
        product = Product.objects.create(name='Test', slug='test', category=category, description='x')
        self.variant = ProductVariant.objects.create(
            product=product, sku='SKU-1', size='S', color='Negro', price_cop=100000
        )
        StockLevel.objects.update_or_create(variant=self.variant, defaults={'available': 5})
        self.customer = Customer.objects.create(email='test@example.com', full_name='Cliente')
        self.address = Address.objects.create(customer=self.customer, line1='Calle 1', city='Bogotá', state='DC')

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
