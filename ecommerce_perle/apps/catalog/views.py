from django.conf import settings
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import generics

from .models import Product, ProductVariant
from .serializers import ProductSerializer


class ProductListApiView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related('category').prefetch_related(
            'images', Prefetch('variants', queryset=ProductVariant.objects.filter(is_active=True).select_related('stock_level'))
        )
        category = self.request.query_params.get('category')
        query = self.request.query_params.get('q')
        if category:
            queryset = queryset.filter(category__slug=category)
        if query:
            queryset = queryset.filter(Q(name__icontains=query) | Q(description__icontains=query))
        return queryset


class ProductDetailApiView(generics.RetrieveAPIView):
    serializer_class = ProductSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related('category').prefetch_related('images', 'variants__stock_level')


@ensure_csrf_cookie
def home(request):
    products = Product.objects.filter(is_active=True).select_related('category').prefetch_related('images', 'variants__stock_level')[:12]
    payload = ProductSerializer(products, many=True).data
    return render(request, 'catalog/home.html', {
        'products': products,
        'products_payload': payload,
        'exchange_rate': settings.CURRENCY_USD_RATE,
    })


@ensure_csrf_cookie
def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related('category').prefetch_related('images', 'variants__stock_level'), slug=slug, is_active=True
    )
    return render(request, 'catalog/product_detail.html', {'product': product})
