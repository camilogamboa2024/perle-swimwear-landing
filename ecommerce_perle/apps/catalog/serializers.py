from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from .models import Product, ProductVariant


class ProductVariantSerializer(serializers.ModelSerializer):
    stock = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = ['id', 'sku', 'size', 'color', 'price_cop', 'compare_at_price_cop', 'is_default', 'stock']

    def get_stock(self, obj):
        try:
            return obj.stock_level.available
        except ObjectDoesNotExist:
            return 0


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
