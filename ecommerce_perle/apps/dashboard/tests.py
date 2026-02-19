from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse


class AdminDashboardFeatureTest(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin = user_model.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='AdminPass123!',
        )
        self.client.force_login(self.admin)

    def test_admin_home_renders_kpi_cards(self):
        response = self.client.get(reverse('admin:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Órdenes hoy')
        self.assertContains(response, 'Ingresos semana')

    @override_settings(ADMIN_SEED_DEMO_ENABLED=True)
    def test_seed_demo_route_is_available_when_enabled(self):
        response = self.client.get(reverse('admin:seed-demo'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Confirmar carga de datos demo')

    @override_settings(ADMIN_SEED_DEMO_ENABLED=False)
    def test_seed_demo_route_returns_404_when_disabled(self):
        response = self.client.get(reverse('admin:seed-demo'))
        self.assertEqual(response.status_code, 404)
