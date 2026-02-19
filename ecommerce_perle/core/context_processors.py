from django.conf import settings


def brand_globals(request):
    return {
        'WHATSAPP_PHONE': getattr(settings, 'WHATSAPP_PHONE', ''),
        'BRAND_NAME': 'Perle Swimwear',
        'BRAND_IG': 'https://instagram.com/perle_swimwear',
        'ADMIN_SEED_DEMO_ENABLED': getattr(settings, 'ADMIN_SEED_DEMO_ENABLED', False),
    }
