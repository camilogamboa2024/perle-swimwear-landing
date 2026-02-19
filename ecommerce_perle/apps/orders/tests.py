import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings

from apps.catalog.models import Category, Product, ProductVariant
from apps.customers.models import Address, Customer
from apps.inventory.models import StockLevel
from apps.orders.models import Order, OrderItem


class CartApiCsrfTest(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        category = Category.objects.create(name='CSRF', slug='csrf')
        product = Product.objects.create(name='CSRF Product', slug='csrf-product', category=category, description='x')
        self.variant = ProductVariant.objects.create(
            product=product,
            sku='SKU-CSRF-1',
            size='M',
            color='Negro',
            price_cop=100000,
            is_active=True,
        )
        StockLevel.objects.update_or_create(variant=self.variant, defaults={'available': 5})

    def _csrf_headers(self):
        response = self.client.get('/')
        token = response.cookies.get('csrftoken').value
        return {'HTTP_X_CSRFTOKEN': token}

    def _add_item(self):
        headers = self._csrf_headers()
        return self.client.post(
            '/api/cart/items/',
            data=json.dumps({'variant_id': self.variant.id, 'quantity': 1}),
            content_type='application/json',
            **headers,
        )

    def test_add_cart_item_requires_csrf(self):
        response = self.client.post(
            '/api/cart/items/',
            data=json.dumps({'variant_id': self.variant.id, 'quantity': 1}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)

    def test_patch_cart_item_requires_csrf(self):
        add_response = self._add_item()
        self.assertEqual(add_response.status_code, 201)
        item_id = add_response.json()['items'][0]['id']
        response = self.client.patch(
            f'/api/cart/items/{item_id}/',
            data=json.dumps({'quantity': 2}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)

    def test_clear_cart_requires_csrf(self):
        add_response = self._add_item()
        self.assertEqual(add_response.status_code, 201)
        response = self.client.post('/api/cart/clear/', data='{}', content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_cart_mutations_succeed_with_csrf(self):
        add_response = self._add_item()
        self.assertEqual(add_response.status_code, 201)
        item_id = add_response.json()['items'][0]['id']
        headers = self._csrf_headers()

        patch_response = self.client.patch(
            f'/api/cart/items/{item_id}/',
            data=json.dumps({'quantity': 2}),
            content_type='application/json',
            **headers,
        )
        self.assertEqual(patch_response.status_code, 200)

        clear_response = self.client.post('/api/cart/clear/', data='{}', content_type='application/json', **headers)
        self.assertEqual(clear_response.status_code, 200)


class CartStockValidationTest(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        category = Category.objects.create(name='Stock', slug='stock')
        product = Product.objects.create(name='Stock Product', slug='stock-product', category=category, description='x')
        self.variant = ProductVariant.objects.create(
            product=product,
            sku='SKU-STOCK-1',
            size='M',
            color='Negro',
            price_cop=100000,
            is_active=True,
        )
        StockLevel.objects.update_or_create(variant=self.variant, defaults={'available': 2})

    def _csrf_headers(self):
        response = self.client.get('/')
        token = response.cookies.get('csrftoken').value
        return {'HTTP_X_CSRFTOKEN': token}

    def test_add_above_stock_returns_400_and_does_not_create_item(self):
        headers = self._csrf_headers()
        response = self.client.post(
            '/api/cart/items/',
            data=json.dumps({'variant_id': self.variant.id, 'quantity': 3}),
            content_type='application/json',
            **headers,
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('stock insuficiente', response.json().get('error', '').lower())

        cart_response = self.client.get('/api/cart/')
        self.assertEqual(cart_response.status_code, 200)
        self.assertEqual(cart_response.json().get('items', []), [])

    def test_patch_above_stock_returns_400_and_keeps_previous_quantity(self):
        headers = self._csrf_headers()
        add_response = self.client.post(
            '/api/cart/items/',
            data=json.dumps({'variant_id': self.variant.id, 'quantity': 1}),
            content_type='application/json',
            **headers,
        )
        self.assertEqual(add_response.status_code, 201)
        item_id = add_response.json()['items'][0]['id']

        patch_response = self.client.patch(
            f'/api/cart/items/{item_id}/',
            data=json.dumps({'quantity': 3}),
            content_type='application/json',
            **headers,
        )
        self.assertEqual(patch_response.status_code, 400)
        self.assertIn('stock insuficiente', patch_response.json().get('error', '').lower())

        cart_response = self.client.get('/api/cart/')
        self.assertEqual(cart_response.status_code, 200)
        self.assertEqual(cart_response.json()['items'][0]['quantity'], 1)


class AuthenticatedCustomerReuseTest(TestCase):
    def setUp(self):
        self.client = Client(HTTP_HOST='127.0.0.1')
        self.User = get_user_model()

    def test_guest_customer_with_same_email_is_reused_when_user_logs_in(self):
        guest_customer = Customer.objects.create(
            email='customer-reuse@example.com',
            full_name='Guest Customer',
        )
        user = self.User.objects.create_user(
            username='reuse-user',
            password='Pass12345!',
            email='customer-reuse@example.com',
        )
        self.client.login(username='reuse-user', password='Pass12345!')

        response = self.client.get('/cart/')
        self.assertEqual(response.status_code, 200)

        guest_customer.refresh_from_db()
        self.assertEqual(guest_customer.user_id, user.id)
        self.assertEqual(Customer.objects.filter(email='customer-reuse@example.com').count(), 1)

    def test_email_collision_with_other_linked_customer_uses_fallback_email(self):
        owner = self.User.objects.create_user(
            username='owner-user',
            password='Pass12345!',
            email='shared-customer@example.com',
        )
        Customer.objects.create(
            user=owner,
            email='shared-customer@example.com',
            full_name='Owner Customer',
        )
        second_user = self.User.objects.create_user(
            username='second-user',
            password='Pass12345!',
            email='shared-customer@example.com',
        )
        self.client.login(username='second-user', password='Pass12345!')

        response = self.client.get('/cart/')
        self.assertEqual(response.status_code, 200)

        second_customer = Customer.objects.get(user=second_user)
        self.assertNotEqual(second_customer.email, 'shared-customer@example.com')
        self.assertIn(f'user-{second_user.id}', second_customer.email)


class CartCrudFlowTest(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        category = Category.objects.create(name='CRUD', slug='crud')
        product = Product.objects.create(name='CRUD Product', slug='crud-product', category=category, description='x')
        self.variant = ProductVariant.objects.create(
            product=product,
            sku='SKU-CRUD-1',
            size='M',
            color='Azul',
            price_cop=89000,
            is_active=True,
        )
        StockLevel.objects.update_or_create(variant=self.variant, defaults={'available': 6})

    def _csrf_headers(self):
        response = self.client.get('/')
        token = response.cookies.get('csrftoken').value
        return {'HTTP_X_CSRFTOKEN': token}

    def test_add_update_delete_and_clear_cart_flow(self):
        headers = self._csrf_headers()
        add_response = self.client.post(
            '/api/cart/items/',
            data=json.dumps({'variant_id': self.variant.id, 'quantity': 1}),
            content_type='application/json',
            **headers,
        )
        self.assertEqual(add_response.status_code, 201)
        item_id = add_response.json()['items'][0]['id']

        patch_response = self.client.patch(
            f'/api/cart/items/{item_id}/',
            data=json.dumps({'quantity': 3}),
            content_type='application/json',
            **headers,
        )
        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(patch_response.json()['items'][0]['quantity'], 3)

        delete_response = self.client.delete(
            f'/api/cart/items/{item_id}/',
            data=json.dumps({}),
            content_type='application/json',
            **headers,
        )
        self.assertEqual(delete_response.status_code, 200)
        self.assertEqual(delete_response.json()['items'], [])

        add_again = self.client.post(
            '/api/cart/items/',
            data=json.dumps({'variant_id': self.variant.id, 'quantity': 1}),
            content_type='application/json',
            **headers,
        )
        self.assertEqual(add_again.status_code, 201)
        clear_response = self.client.post('/api/cart/clear/', data=json.dumps({}), content_type='application/json', **headers)
        self.assertEqual(clear_response.status_code, 200)
        self.assertEqual(clear_response.json()['items'], [])


class OrderConfirmationSessionGuardTest(TestCase):
    def setUp(self):
        self.client = Client()
        category = Category.objects.create(name='Guard', slug='guard')
        product = Product.objects.create(name='Guard Product', slug='guard-product', category=category, description='x')
        variant = ProductVariant.objects.create(
            product=product,
            sku='SKU-GUARD-1',
            size='S',
            color='Negro',
            price_cop=120000,
            is_active=True,
        )
        StockLevel.objects.update_or_create(variant=variant, defaults={'available': 4})
        customer = Customer.objects.create(email='guard@example.com', full_name='Guard Customer')
        address = Address.objects.create(customer=customer, line1='Calle 1', city='Bogotá', state='DC')
        self.order = Order.objects.create(
            customer=customer,
            address=address,
            status=Order.CONFIRMED,
            subtotal=120000,
            discount_total=0,
            grand_total=120000,
            session_key='',
            whatsapp_message='Hola Perle',
        )
        OrderItem.objects.create(
            order=self.order,
            variant=variant,
            quantity=1,
            unit_price=120000,
            line_total=120000,
        )

        session = self.client.session
        session['order_access'] = 'ok'
        session.save()
        self.order.session_key = session.session_key
        self.order.save(update_fields=['session_key'])

    def test_confirmation_allows_owner_session(self):
        response = self.client.get(f'/orders/confirmation/{self.order.public_id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(self.order.public_id))

    def test_confirmation_blocks_other_session(self):
        other_client = Client()
        other_client.get('/')
        response = other_client.get(f'/orders/confirmation/{self.order.public_id}/')
        self.assertEqual(response.status_code, 404)

    @override_settings(WHATSAPP_PHONE='')
    def test_confirmation_hides_whatsapp_link_when_phone_missing(self):
        response = self.client.get(f'/orders/confirmation/{self.order.public_id}/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'wa.me/')

    @override_settings(WHATSAPP_PHONE='573001112233')
    def test_confirmation_shows_whatsapp_link_when_phone_is_set(self):
        response = self.client.get(f'/orders/confirmation/{self.order.public_id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'wa.me/573001112233')
