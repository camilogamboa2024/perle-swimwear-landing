from django.contrib.admin import helpers
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Category, Product, ProductVariant
from apps.inventory.models import InventoryMovement, StockLevel


class InventoryAdminAdjustStockTest(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin = user_model.objects.create_superuser(
            username='inventory-admin',
            email='inventory-admin@example.com',
            password='AdminPass123!',
        )
        self.client.force_login(self.admin)

        category = Category.objects.create(name='Inventory Admin', slug='inventory-admin')
        product = Product.objects.create(name='Inventory Product', slug='inventory-product', category=category, description='x')
        variant = ProductVariant.objects.create(
            product=product,
            sku='SKU-INV-ADMIN',
            size='M',
            color='Negro',
            price_usd_cents=99000,
            is_active=True,
        )
        self.stock, _ = StockLevel.objects.update_or_create(variant=variant, defaults={'available': 1})

    def test_adjust_stock_creates_adjust_movement_and_never_goes_negative(self):
        changelist_url = reverse('admin:inventory_stocklevel_changelist')
        selected_key = helpers.ACTION_CHECKBOX_NAME

        first_step = self.client.post(
            changelist_url,
            data={
                'action': 'adjust_stock',
                selected_key: [self.stock.pk],
            },
        )
        self.assertEqual(first_step.status_code, 200)
        self.assertContains(first_step, 'Confirmar ajuste de stock')
        self.assertContains(first_step, 'Proyección')

        apply_step = self.client.post(
            changelist_url,
            data={
                'action': 'adjust_stock',
                'apply': '1',
                selected_key: [self.stock.pk],
                'delta': -10,
                'reason': 'Corrección operativa',
            },
            follow=True,
        )
        self.assertEqual(apply_step.status_code, 200)

        self.stock.refresh_from_db()
        self.assertEqual(self.stock.available, 0)

        movement = InventoryMovement.objects.filter(variant=self.stock.variant, movement_type=InventoryMovement.ADJUST).latest('created_at')
        self.assertEqual(movement.reason, 'Corrección operativa')
        self.assertEqual(movement.quantity, -1)
