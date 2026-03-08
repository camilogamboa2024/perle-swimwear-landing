from rest_framework import serializers

from apps.catalog.models import ProductVariant
from .money import cents_to_usd_decimal
from .models import Cart, CartItem
from .services import calculate_cart_totals


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='variant.product.name', read_only=True)
    size = serializers.CharField(source='variant.size', read_only=True)
    color = serializers.CharField(source='variant.color', read_only=True)
    unit_price_cents = serializers.IntegerField(source='variant.price_usd_cents', read_only=True)
    unit_price = serializers.IntegerField(source='variant.price_usd_cents', read_only=True)
    unit_price_usd = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            'id',
            'variant',
            'quantity',
            'product_name',
            'size',
            'color',
            'unit_price_cents',
            'unit_price_usd',
            'unit_price',
        ]

    def get_unit_price_usd(self, obj):
        return f'{cents_to_usd_decimal(obj.variant.price_usd_cents):.2f}'


class AddCartItemSerializer(serializers.Serializer):
    variant_id = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.filter(is_active=True), source='variant')
    quantity = serializers.IntegerField(min_value=1)


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True)
    totals = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'currency', 'items', 'totals']

    def get_totals(self, obj):
        totals = calculate_cart_totals(obj, None)
        return {
            **totals,
            'subtotal_usd': f"{cents_to_usd_decimal(totals['subtotal_cents']):.2f}",
            'discount_total_usd': f"{cents_to_usd_decimal(totals['discount_total_cents']):.2f}",
            'grand_total_usd': f"{cents_to_usd_decimal(totals['grand_total_cents']):.2f}",
        }
