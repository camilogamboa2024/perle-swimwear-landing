from django.conf import settings
from django.contrib import admin, messages
from django.core.management import call_command
from django.http import Http404
from django.shortcuts import redirect
from django.template.response import TemplateResponse


def seed_demo_admin_view(request):
    if not settings.ADMIN_SEED_DEMO_ENABLED:
        raise Http404('Operación no habilitada.')

    if request.method == 'POST':
        try:
            call_command('seed_demo')
        except Exception as exc:  # noqa: BLE001
            messages.error(request, f'Falló seed_demo: {exc}')
        else:
            messages.success(request, 'Datos demo cargados correctamente.')
        return redirect('admin:index')

    context = {
        **admin.site.each_context(request),
        'title': 'Confirmar carga de datos demo',
    }
    return TemplateResponse(request, 'admin/seed_demo_confirm.html', context)
