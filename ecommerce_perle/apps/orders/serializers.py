from rest_framework import serializers

from apps.catalog.models import ProductVariant
from .models import Cart, CartItem
from .services import calculate_cart_totals


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='variant.product.name', read_only=True)
    size = serializers.CharField(source='variant.size', read_only=True)
    color = serializers.CharField(source='variant.color', read_only=True)
    unit_price = serializers.IntegerField(source='variant.price_cop', read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'variant', 'quantity', 'product_name', 'size', 'color', 'unit_price']


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
        return calculate_cart_totals(obj, None)
