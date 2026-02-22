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
    urlpatterns.insert(
        1,
        path('', include('two_factor.urls', namespace='two_factor')),
    )
