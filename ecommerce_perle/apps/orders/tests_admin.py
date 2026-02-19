from django.contrib.admin import helpers
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Category, Product, ProductVariant
from apps.customers.models import Address, Customer
from apps.inventory.models import StockLevel
from apps.orders.models import Order, OrderItem, OrderStatusHistory


class OrderAdminActionsTest(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin = user_model.objects.create_superuser(
            username='ops-admin',
            email='ops-admin@example.com',
            password='AdminPass123!',
        )
        self.client.force_login(self.admin)

        category = Category.objects.create(name='Admin Actions', slug='admin-actions')
        product = Product.objects.create(name='Producto Admin', slug='producto-admin', category=category, description='x')
        self.variant = ProductVariant.objects.create(
            product=product,
            sku='SKU-ADMIN-ACT',
            size='L',
            color='Arena',
            price_cop=145000,
            is_active=True,
        )
        StockLevel.objects.update_or_create(variant=self.variant, defaults={'available': 5})
        customer = Customer.objects.create(email='order-admin@example.com', full_name='Order Admin Customer')
        address = Address.objects.create(customer=customer, line1='Calle 1', city='Bogotá', state='DC')
        self.order = Order.objects.create(
            customer=customer,
            address=address,
            status=Order.PENDING,
            subtotal=145000,
            discount_total=0,
            grand_total=145000,
        )
        OrderItem.objects.create(
            order=self.order,
            variant=self.variant,
            quantity=1,
            unit_price=145000,
            line_total=145000,
        )

    def test_mark_paid_action_sets_paid_at_and_creates_history(self):
        changelist_url = reverse('admin:orders_order_changelist')
        selected_key = helpers.ACTION_CHECKBOX_NAME
        initial_response = self.client.post(
            changelist_url,
            data={
                'action': 'mark_paid',
                selected_key: [self.order.pk],
            },
        )
        self.assertEqual(initial_response.status_code, 200)
        self.assertContains(initial_response, 'Confirmar cambio')

        apply_response = self.client.post(
            changelist_url,
            data={
                'action': 'mark_paid',
                'apply': '1',
                selected_key: [self.order.pk],
            },
            follow=True,
        )
        self.assertEqual(apply_response.status_code, 200)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.PAID)
        self.assertIsNotNone(self.order.paid_at)
        self.assertTrue(
            OrderStatusHistory.objects.filter(
                order=self.order,
                from_status=Order.PENDING,
                to_status=Order.PAID,
            ).exists()
        )

    def test_mark_shipped_action_updates_status(self):
        self.order.status = Order.PAID
        self.order.save(update_fields=['status'])

        changelist_url = reverse('admin:orders_order_changelist')
        selected_key = helpers.ACTION_CHECKBOX_NAME
        self.client.post(
            changelist_url,
            data={
                'action': 'mark_shipped',
                selected_key: [self.order.pk],
            },
        )
        self.client.post(
            changelist_url,
            data={
                'action': 'mark_shipped',
                'apply': '1',
                selected_key: [self.order.pk],
            },
            follow=True,
        )
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.SHIPPED)
