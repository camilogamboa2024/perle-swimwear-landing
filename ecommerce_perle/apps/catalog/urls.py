from django.urls import path
from .views import ProductDetailApiView, ProductListApiView, home, product_detail

urlpatterns = [
    path('', home, name='home'),
    path('product/<slug:slug>/', product_detail, name='product-detail'),
    path('api/products/', ProductListApiView.as_view(), name='api-products'),
    path('api/products/<slug:slug>/', ProductDetailApiView.as_view(), name='api-product-detail'),
]
