from rest_framework.authentication import SessionAuthentication


class EnforcedCsrfSessionAuthentication(SessionAuthentication):
    """
    Force CSRF validation for session-based requests, including anonymous sessions.
    """

    def authenticate(self, request):
        self.enforce_csrf(request)
        return super().authenticate(request)
