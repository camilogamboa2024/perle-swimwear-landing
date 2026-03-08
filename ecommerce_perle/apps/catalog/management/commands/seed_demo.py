from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import Category, Product, ProductImage, ProductVariant
from apps.inventory.models import StockLevel


DEMO_PRODUCTS = [
    {
        'name': 'Bikini Reversible Aura',
        'slug': 'bikini-reversible-aura',
        'description': 'Bikini reversible con ajuste cómodo y acabado premium.',
        'image': 'https://images.unsplash.com/photo-1515377905703-c4788e51af15?w=900&q=80',
        'base_price_usd_cents': 4914,
    },
    {
        'name': 'One-Piece Solé',
        'slug': 'one-piece-sole',
        'description': 'Enterizo elegante con soporte suave para uso prolongado.',
        'image': 'https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=900&q=80',
        'base_price_usd_cents': 6214,
    },
    {
        'name': 'Trikini Nacar',
        'slug': 'trikini-nacar',
        'description': 'Trikini de silueta estilizada con detalles minimalistas.',
        'image': 'https://images.unsplash.com/photo-1464863979621-258859e62245?w=900&q=80',
        'base_price_usd_cents': 5434,
    },
]


class Command(BaseCommand):
    help = 'Crea datos demo de catálogo e inventario para smoke tests.'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Elimina productos demo antes de recrearlos.')

    @transaction.atomic
    def handle(self, *args, **options):
        category, _ = Category.objects.get_or_create(name='Nueva Colección', defaults={'slug': 'nueva-coleccion'})

        if options['reset']:
            Product.objects.filter(slug__in=[p['slug'] for p in DEMO_PRODUCTS]).delete()

        for data in DEMO_PRODUCTS:
            product, _ = Product.objects.update_or_create(
                slug=data['slug'],
                defaults={
                    'name': data['name'],
                    'category': category,
                    'description': data['description'],
                    'is_active': True,
                },
            )
            ProductImage.objects.update_or_create(
                product=product,
                sort_order=0,
                defaults={'image_url': data['image'], 'alt_text': data['name']},
            )

            for size in ['S', 'M', 'L']:
                for color in ['Negro', 'Marfil']:
                    sku = f"{product.slug[:10].upper()}-{size}-{color[:3].upper()}"
                    variant, _ = ProductVariant.objects.update_or_create(
                        sku=sku,
                        defaults={
                            'product': product,
                            'size': size,
                            'color': color,
                            'price_usd_cents': data['base_price_usd_cents'],
                            'compare_at_price_usd_cents': data['base_price_usd_cents'] + 780,
                            'is_default': size == 'M' and color == 'Negro',
                            'is_active': True,
                        },
                    )
                    StockLevel.objects.update_or_create(variant=variant, defaults={'available': 8})

        self.stdout.write(self.style.SUCCESS('Datos demo de catálogo creados/actualizados correctamente.'))
