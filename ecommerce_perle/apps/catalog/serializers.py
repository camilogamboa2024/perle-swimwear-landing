from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from apps.orders.money import cents_to_usd_decimal

from .models import Product, ProductVariant


class ProductVariantSerializer(serializers.ModelSerializer):
    stock = serializers.SerializerMethodField()
    price_usd = serializers.SerializerMethodField()
    compare_at_price_usd = serializers.SerializerMethodField()
    # Legacy aliases kept during transition window.
    price_cop = serializers.IntegerField(source='price_usd_cents', read_only=True)
    compare_at_price_cop = serializers.IntegerField(source='compare_at_price_usd_cents', read_only=True)

    class Meta:
        model = ProductVariant
        fields = [
            'id',
            'sku',
            'size',
            'color',
            'price_usd_cents',
            'compare_at_price_usd_cents',
            'price_usd',
            'compare_at_price_usd',
            'price_cop',
            'compare_at_price_cop',
            'is_default',
            'stock',
        ]

    def get_stock(self, obj):
        try:
            return obj.stock_level.available
        except ObjectDoesNotExist:
            return 0

    def get_price_usd(self, obj):
        return f'{cents_to_usd_decimal(obj.price_usd_cents):.2f}'

    def get_compare_at_price_usd(self, obj):
        if obj.compare_at_price_usd_cents is None:
            return None
        return f'{cents_to_usd_decimal(obj.compare_at_price_usd_cents):.2f}'


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source='category.slug')
    variants = ProductVariantSerializer(many=True)
    image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'description', 'category', 'variants', 'image']

    def get_image(self, obj):
        first = obj.images.first()
        return first.image_url if first else ''
