from django.conf import settings


def brand_globals(request):
    return {
        'WHATSAPP_PHONE': getattr(settings, 'WHATSAPP_PHONE', ''),
        'BRAND_NAME': 'Perle Swimwear',
        'BRAND_IG': 'https://instagram.com/perle_swimwear',
        'ADMIN_SEED_DEMO_ENABLED': getattr(settings, 'ADMIN_SEED_DEMO_ENABLED', False),
        'MARKET_COUNTRY_NAME': getattr(settings, 'MARKET_COUNTRY_NAME', 'Panama'),
        'MARKET_COUNTRY_LABEL': getattr(settings, 'MARKET_COUNTRY_LABEL', 'Panamá'),
        'MARKET_CITY': getattr(settings, 'MARKET_CITY', 'Ciudad de Panamá'),
        'MARKET_STATE': getattr(settings, 'MARKET_STATE', 'Panamá'),
    }
