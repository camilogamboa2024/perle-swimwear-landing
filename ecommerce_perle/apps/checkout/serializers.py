from rest_framework import serializers


class CheckoutConfirmSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=120)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    line1 = serializers.CharField(max_length=180)
    city = serializers.CharField(max_length=80)
    state = serializers.CharField(max_length=80)
    coupon_code = serializers.CharField(max_length=40, required=False, allow_blank=True)
    payment_method = serializers.ChoiceField(choices=['whatsapp', 'manual', 'wompi', 'stripe'], default='whatsapp')
