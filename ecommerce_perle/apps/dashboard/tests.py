import importlib.util
from unittest import skipUnless

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.catalog.models import Category, Product, ProductVariant
from apps.customers.models import Address, Customer
from apps.inventory.models import StockLevel
from apps.orders.models import Order, OrderItem

HAS_TWO_FACTOR_PACKAGE = importlib.util.find_spec('two_factor') is not None


class AdminDashboardFeatureTest(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin = user_model.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='AdminPass123!',
        )
        self.client.force_login(self.admin)
        category = Category.objects.create(name='Admin QA', slug='admin-qa')
        product = Product.objects.create(
            name='Traje QA',
            slug='traje-qa',
            category=category,
            description='x',
        )
        self.variant = ProductVariant.objects.create(
            product=product,
            sku='SKU-ADMIN-QA',
            size='M',
            color='Negro',
            price_cop=120000,
            is_active=True,
        )
        StockLevel.objects.update_or_create(variant=self.variant, defaults={'available': 2})
        customer = Customer.objects.create(email='dashboard-admin@example.com', full_name='Cliente Dashboard')
        address = Address.objects.create(customer=customer, line1='Calle 100', city='Bogotá', state='DC')
        order = Order.objects.create(
            customer=customer,
            address=address,
            status=Order.PENDING,
            subtotal=120000,
            discount_total=0,
            grand_total=120000,
        )
        OrderItem.objects.create(
            order=order,
            variant=self.variant,
            quantity=1,
            unit_price=120000,
            line_total=120000,
        )

    def test_admin_home_renders_kpi_cards(self):
        response = self.client.get(reverse('admin:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Órdenes hoy')
        self.assertContains(response, 'Ingresos semana')
        self.assertContains(response, 'Ticket promedio semana')
        self.assertContains(response, 'kpi-series-7d')
        self.assertContains(response, 'kpi-series-30d')
        self.assertContains(response, 'kpi-status-distribution')
        self.assertContains(response, 'perle-orders-7d-chart')
        self.assertContains(response, 'perle-revenue-30d-chart')
        self.assertContains(response, 'brand/perle-logo-admin.png')
        self.assertNotContains(response, 'Módulos administrativos')

    @override_settings(ADMIN_SEED_DEMO_ENABLED=True)
    def test_seed_demo_route_is_available_when_enabled(self):
        response = self.client.get(reverse('admin:seed-demo'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Confirmar carga de datos demo')

    @override_settings(ADMIN_SEED_DEMO_ENABLED=False)
    def test_seed_demo_route_returns_404_when_disabled(self):
        response = self.client.get(reverse('admin:seed-demo'))
        self.assertEqual(response.status_code, 404)

    def test_admin_login_and_orders_changelist_are_in_spanish(self):
        self.client.logout()
        login_response = self.client.get(reverse('admin:login'))
        self.assertEqual(login_response.status_code, 200)
        self.assertContains(login_response, 'Iniciar sesión')
        self.assertContains(login_response, 'Nombre de usuario')
        self.assertContains(login_response, 'Contraseña')
        self.assertContains(login_response, 'brand/perle-wordmark.png')
        self.assertContains(login_response, 'admin/perle_admin_v2.css')
        self.assertContains(login_response, 'admin/perle_admin.js')

        self.client.force_login(self.admin)
        dashboard_response = self.client.get(reverse('admin:index'))
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertContains(dashboard_response, 'perle-admin-dashboard')
        self.assertContains(dashboard_response, 'admin/perle_dashboard_v2.js')
        self.assertContains(dashboard_response, 'brand/perle-logo-admin.png')
        self.assertNotContains(dashboard_response, 'Módulos administrativos')

        orders_response = self.client.get(reverse('admin:orders_order_changelist'))
        self.assertEqual(orders_response.status_code, 200)
        self.assertContains(orders_response, 'Órdenes')
        self.assertContains(orders_response, 'perle-pill')

    @override_settings(ADMIN_MFA_REQUIRED=True, HAS_TWO_FACTOR=True)
    def test_admin_redirects_staff_to_mfa_when_enforced(self):
        response = self.client.get(reverse('admin:index'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/account/', response.url)
        self.assertIn('next=%2Fadmin%2F', response.url)

    @skipUnless(HAS_TWO_FACTOR_PACKAGE, 'django-two-factor-auth no disponible en este entorno.')
    @override_settings(ADMIN_MFA_REQUIRED=True, HAS_TWO_FACTOR=True)
    def test_two_factor_account_routes_are_live_and_admin_redirects_to_setup(self):
        login_url = reverse('two_factor:login')
        self.assertEqual(login_url, '/account/login/')
        login_response = self.client.get(login_url)
        self.assertEqual(login_response.status_code, 200)

        response = self.client.get(reverse('admin:index'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('two_factor:setup')))
        self.assertIn('next=%2Fadmin%2F', response.url)
