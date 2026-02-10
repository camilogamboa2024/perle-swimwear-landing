from django.test import TestCase, override_settings

from apps.catalog.models import Category, Product, ProductVariant
from apps.inventory.models import StockLevel


class WhatsAppVisibilityTemplateTest(TestCase):
    @override_settings(WHATSAPP_PHONE='')
    def test_home_hides_wa_links_when_phone_empty(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'wa.me/')

    @override_settings(WHATSAPP_PHONE='573001112233')
    def test_home_shows_wa_links_when_phone_set(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'wa.me/573001112233')


class ActiveVariantsVisibilityTest(TestCase):
    def setUp(self):
        category = Category.objects.create(name='Bikinis', slug='bikinis')
        self.product = Product.objects.create(name='Producto', slug='producto', category=category, description='Desc')
        self.active_variant = ProductVariant.objects.create(
            product=self.product,
            sku='SKU-ACTIVA',
            size='M',
            color='Negro',
            price_cop=100000,
            is_active=True,
        )
        self.inactive_variant = ProductVariant.objects.create(
            product=self.product,
            sku='SKU-INACTIVA',
            size='L',
            color='Marfil',
            price_cop=120000,
            is_active=False,
        )
        StockLevel.objects.update_or_create(variant=self.active_variant, defaults={'available': 3})
        StockLevel.objects.update_or_create(variant=self.inactive_variant, defaults={'available': 3})

    def test_home_exposes_only_active_variant_for_add_to_cart(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'data-add-cart="{self.active_variant.id}"')
        self.assertNotContains(response, f'data-add-cart="{self.inactive_variant.id}"')

    def test_product_detail_exposes_only_active_variants(self):
        response = self.client.get(f'/product/{self.product.slug}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'data-add-cart="{self.active_variant.id}"')
        self.assertNotContains(response, f'data-add-cart="{self.inactive_variant.id}"')

    def test_product_detail_api_excludes_inactive_variants(self):
        response = self.client.get(f'/api/products/{self.product.slug}/')
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        variant_ids = {variant['id'] for variant in payload['variants']}
        self.assertIn(self.active_variant.id, variant_ids)
        self.assertNotIn(self.inactive_variant.id, variant_ids)
