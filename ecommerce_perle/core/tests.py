from datetime import timedelta

from django.test import Client, TestCase, override_settings


@override_settings(
    AUTHENTICATION_BACKENDS=[
        'axes.backends.AxesStandaloneBackend',
        'django.contrib.auth.backends.ModelBackend',
    ],
    AXES_ENABLED=True,
    AXES_FAILURE_LIMIT=2,
    AXES_COOLOFF_TIME=timedelta(hours=1),
    AXES_ONLY_ADMIN_SITE=True,
)
class AdminLockoutSecurityTest(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)

    def _login_headers(self):
        response = self.client.get('/admin/login/')
        token = response.cookies.get('csrftoken').value
        return token, {'HTTP_REFERER': 'http://testserver/admin/login/'}

    def test_admin_login_lockout_page_is_rendered_after_repeated_failures(self):
        for _ in range(2):
            token, headers = self._login_headers()
            response = self.client.post(
                '/admin/login/?next=/admin/',
                data={
                    'username': 'invalid-admin',
                    'password': 'wrong-password-123',
                    'this_is_the_login_form': '1',
                    'next': '/admin/',
                    'csrfmiddlewaretoken': token,
                },
                **headers,
            )

        self.assertIn(response.status_code, {200, 429})
        body = response.content.decode('utf-8')
        self.assertIn('Acceso temporalmente bloqueado', body)
        self.assertIn('demasiados intentos fallidos', body)
