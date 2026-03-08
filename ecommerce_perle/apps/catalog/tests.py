from django.test import TestCase, override_settings

from apps.catalog.admin import ProductVariantPricingForm
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
            price_usd_cents=100000,
            is_active=True,
        )
        self.inactive_variant = ProductVariant.objects.create(
            product=self.product,
            sku='SKU-INACTIVA',
            size='L',
            color='Marfil',
            price_usd_cents=120000,
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
        active_variant_payload = next(variant for variant in payload['variants'] if variant['id'] == self.active_variant.id)
        self.assertIn('price_usd_cents', active_variant_payload)
        self.assertIn('compare_at_price_usd_cents', active_variant_payload)
        self.assertIn('price_usd', active_variant_payload)
        self.assertIn('price_cop', active_variant_payload)
        self.assertEqual(active_variant_payload['price_usd_cents'], active_variant_payload['price_cop'])


class TemplateRegressionTest(TestCase):
    def test_base_template_references_new_logo_and_favicon_png_assets(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "brand/perle-wordmark.png")
        self.assertContains(response, "brand/favicon.png")
        self.assertContains(response, 'Saltar al contenido principal')

    def test_home_currency_labels_are_usd(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'USD')
        self.assertNotContains(response, 'COP')

    @override_settings(WHATSAPP_PHONE='')
    def test_home_insiders_panel_does_not_fake_newsletter_submit_when_unavailable(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'action="#"')
        self.assertContains(response, 'Novedades y asesoría disponibles por nuestros canales oficiales.')

    def test_checkout_template_renders_expected_controls(self):
        response = self.client.get('/checkout/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-testid="checkout-page"')
        self.assertContains(response, 'id="checkout-form"')
        self.assertContains(response, 'id="checkout-result"')
        self.assertContains(response, 'id="checkout-alert"')
        self.assertContains(response, 'name="coupon_code"')
        self.assertContains(response, 'Moneda de cobro: USD')

    def test_cart_template_renders_cart_data_hooks(self):
        response = self.client.get('/cart/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-cart-page')
        self.assertContains(response, 'data-testid="go-checkout"')
        self.assertContains(response, 'id="cart-items"')
        self.assertContains(response, 'id="cart-status"')


class WebSecurityHeadersTest(TestCase):
    def test_storefront_responses_include_report_only_csp_in_monitor_phase(self):
        for path in ('/', '/checkout/'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertIn('Content-Security-Policy-Report-Only', response)
            self.assertNotIn('Content-Security-Policy', response)
            self.assertIn("default-src 'self'", response['Content-Security-Policy-Report-Only'])
            self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
            self.assertEqual(response['X-Frame-Options'], 'DENY')
            self.assertIn('strict-origin-when-cross-origin', response['Referrer-Policy'])

    @override_settings(SECURITY_PHASE='enforce')
    def test_storefront_responses_include_enforced_csp_in_enforce_phase(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Content-Security-Policy', response)
        self.assertNotIn('Content-Security-Policy-Report-Only', response)
        self.assertIn("default-src 'self'", response['Content-Security-Policy'])

    @override_settings(WHATSAPP_PHONE='573001112233')
    def test_external_blank_links_include_noopener_noreferrer(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'rel="noopener noreferrer"')
        self.assertContains(response, 'href="https://wa.me/573001112233"')


class ProductVariantPricingFormTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Form', slug='form')
        self.product = Product.objects.create(name='Producto Form', slug='producto-form', category=self.category, description='x')

    def test_admin_form_converts_decimal_usd_to_cents(self):
        form = ProductVariantPricingForm(
            data={
                'product': self.product.id,
                'sku': 'SKU-FORM-1',
                'size': 'M',
                'color': 'Aqua',
                'price_usd': '49.14',
                'compare_at_price_usd': '56.94',
                'is_default': 'on',
                'is_active': 'on',
            }
        )
        self.assertTrue(form.is_valid(), form.errors.as_json())
        variant = form.save()
        self.assertEqual(variant.price_usd_cents, 4914)
        self.assertEqual(variant.compare_at_price_usd_cents, 5694)
