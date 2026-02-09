from django.test import TestCase, override_settings


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
