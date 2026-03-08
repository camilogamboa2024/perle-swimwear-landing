from urllib.parse import urlencode

from django.conf import settings
from django.shortcuts import redirect
from django.urls import NoReverseMatch, reverse

try:
    from django_otp import user_has_device as _user_has_device
except Exception:  # pragma: no cover - optional dependency fallback
    def _user_has_device(user):  # type: ignore[no-redef]
        return False


class AdminMfaEnforcementMiddleware:
    """
    Redirect staff users to MFA setup/login when admin MFA is enforced.
    """

    ADMIN_PREFIX = '/admin/'
    ACCOUNT_PREFIX = '/account/'
    ADMIN_EXEMPT_PREFIXES = (
        '/admin/login/',
        '/admin/logout/',
        '/admin/jsi18n/',
        '/admin/password_reset/',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not self._should_enforce(request):
            return self.get_response(request)

        target_url = self._build_mfa_redirect_url(request)
        return redirect(target_url)

    def _should_enforce(self, request):
        if not getattr(settings, 'ADMIN_MFA_REQUIRED', False):
            return False
        if not getattr(settings, 'HAS_TWO_FACTOR', False):
            return False

        path = request.path
        if path.startswith(self.ACCOUNT_PREFIX):
            return False
        if not path.startswith(self.ADMIN_PREFIX):
            return False
        if any(path.startswith(prefix) for prefix in self.ADMIN_EXEMPT_PREFIXES):
            return False

        user = request.user
        if not user.is_authenticated or not user.is_staff:
            return False

        is_verified = getattr(user, 'is_verified', None)
        if callable(is_verified) and is_verified():
            return False
        return True

    def _build_mfa_redirect_url(self, request):
        user = request.user
        route_names = ['two_factor:setup', 'two_factor:login']
        fallback_path = '/account/setup/'
        if _user_has_device(user):
            route_names = ['two_factor:login']
            fallback_path = '/account/login/'

        resolved_path = fallback_path
        for route_name in route_names:
            try:
                resolved_path = reverse(route_name)
                break
            except NoReverseMatch:
                continue

        separator = '&' if '?' in resolved_path else '?'
        return f"{resolved_path}{separator}{urlencode({'next': request.get_full_path()})}"
