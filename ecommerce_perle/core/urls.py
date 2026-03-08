from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.catalog.urls')),
    path('', include('apps.orders.urls')),
    path('checkout/', include('apps.checkout.urls')),
    path('legal/terms/', TemplateView.as_view(template_name='legal/terms.html'), name='legal-terms'),
    path('legal/privacy/', TemplateView.as_view(template_name='legal/privacy.html'), name='legal-privacy'),
    path('legal/shipping-returns/', TemplateView.as_view(template_name='legal/shipping_returns.html'), name='legal-shipping-returns'),
]

if settings.HAS_TWO_FACTOR:
    from two_factor import urls as two_factor_urls

    two_factor_patterns = getattr(two_factor_urls, 'urlpatterns', [])
    two_factor_app_name = getattr(two_factor_urls, 'app_name', 'two_factor')
    if isinstance(two_factor_patterns, tuple) and len(two_factor_patterns) == 2:
        first, second = two_factor_patterns
        if isinstance(first, str) and isinstance(second, (list, tuple)):
            two_factor_app_name = first
            two_factor_patterns = second
        elif isinstance(first, (list, tuple)) and isinstance(second, str):
            two_factor_patterns = first
            two_factor_app_name = second

    urlpatterns.insert(
        1,
        path('', include((two_factor_patterns, two_factor_app_name), namespace='two_factor')),
    )
