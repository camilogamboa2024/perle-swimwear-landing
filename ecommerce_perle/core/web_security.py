from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class WebSecurityHeadersMiddleware:
    """
    Enforce storefront security headers without depending on optional CSP packages.
    """

    DEFAULT_SKIP_PREFIXES = (
        '/admin/',
        '/account/',
        '/static/',
        '/media/',
    )

    def __init__(self, get_response):
        self.get_response = get_response
        self.skip_prefixes = tuple(
            getattr(settings, 'WEB_SECURITY_SKIP_PREFIXES', self.DEFAULT_SKIP_PREFIXES)
        )
        self._validate_enforce_mode()

    def __call__(self, request):
        response = self.get_response(request)
        if not self._should_apply(request.path):
            return response

        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), camera=(), microphone=()'

        phase = getattr(settings, 'SECURITY_PHASE', 'monitor')
        csp_policy = self._build_csp_policy(getattr(settings, 'WEB_SECURITY_CSP_DIRECTIVES', {}))
        if phase == 'enforce' and not csp_policy:
            raise ImproperlyConfigured('SECURITY_PHASE=enforce requiere una politica CSP valida.')

        if csp_policy:
            if phase == 'monitor':
                response['Content-Security-Policy-Report-Only'] = csp_policy
                if response.has_header('Content-Security-Policy'):
                    del response['Content-Security-Policy']
            else:
                response['Content-Security-Policy'] = csp_policy
                if response.has_header('Content-Security-Policy-Report-Only'):
                    del response['Content-Security-Policy-Report-Only']

        return response

    def _should_apply(self, path):
        return not any(path.startswith(prefix) for prefix in self.skip_prefixes)

    @staticmethod
    def _build_csp_policy(directives):
        if not isinstance(directives, dict):
            return ''

        chunks = []
        for directive, sources in directives.items():
            if not directive:
                continue
            if isinstance(sources, str):
                value = sources.strip()
            else:
                source_values = [str(source).strip() for source in sources if str(source).strip()]
                value = ' '.join(source_values)
            if value:
                chunks.append(f'{directive} {value}')
            else:
                chunks.append(directive)
        return '; '.join(chunks)

    def _validate_enforce_mode(self):
        if getattr(settings, 'SECURITY_PHASE', 'monitor') != 'enforce':
            return
        csp_policy = self._build_csp_policy(getattr(settings, 'WEB_SECURITY_CSP_DIRECTIVES', {}))
        if not csp_policy:
            raise ImproperlyConfigured('SECURITY_PHASE=enforce requiere una politica CSP valida.')
