from django.contrib import admin
from django.urls import path

from .views import seed_demo_admin_view


if not getattr(admin.site, '_perle_custom_urls_registered', False):
    _default_get_urls = admin.site.get_urls

    def _get_urls():
        custom_urls = [
            path(
                'ops/seed-demo/',
                admin.site.admin_view(seed_demo_admin_view),
                name='seed-demo',
            ),
        ]
        return custom_urls + _default_get_urls()

    admin.site.get_urls = _get_urls
    admin.site._perle_custom_urls_registered = True
