from decimal import Decimal, ROUND_HALF_UP

from django.db import migrations

COP_TO_USD_RATE = Decimal('0.00026')
HUNDRED = Decimal('100')


def _cop_to_usd_cents(value):
    if value is None:
        return None
    cents = (Decimal(value) * COP_TO_USD_RATE * HUNDRED).quantize(
        Decimal('1'),
        rounding=ROUND_HALF_UP,
    )
    return int(cents)


def convert_catalog_prices_to_usd_cents(apps, schema_editor):
    ProductVariant = apps.get_model('catalog', 'ProductVariant')
    to_update = []
    for variant in ProductVariant.objects.all().iterator():
        variant.price_usd_cents = _cop_to_usd_cents(variant.price_usd_cents)
        variant.compare_at_price_usd_cents = _cop_to_usd_cents(variant.compare_at_price_usd_cents)
        to_update.append(variant)
        if len(to_update) >= 500:
            ProductVariant.objects.bulk_update(
                to_update,
                ['price_usd_cents', 'compare_at_price_usd_cents'],
            )
            to_update.clear()
    if to_update:
        ProductVariant.objects.bulk_update(
            to_update,
            ['price_usd_cents', 'compare_at_price_usd_cents'],
        )


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0003_alter_category_options_alter_product_options_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='productvariant',
            old_name='price_cop',
            new_name='price_usd_cents',
        ),
        migrations.RenameField(
            model_name='productvariant',
            old_name='compare_at_price_cop',
            new_name='compare_at_price_usd_cents',
        ),
        migrations.RunPython(convert_catalog_prices_to_usd_cents, migrations.RunPython.noop),
    ]
