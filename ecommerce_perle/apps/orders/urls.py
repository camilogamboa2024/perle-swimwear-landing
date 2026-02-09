from django.urls import path
from .views import CartApiView, CartClearApiView, CartItemDetailApiView, CartItemsApiView, cart_page, order_confirmation

urlpatterns = [
    path('cart/', cart_page, name='cart-page'),
    path('orders/confirmation/<uuid:public_id>/', order_confirmation, name='order-confirmation'),
    path('api/cart/', CartApiView.as_view(), name='api-cart'),
    path('api/cart/items/', CartItemsApiView.as_view(), name='api-cart-items'),
    path('api/cart/items/<int:item_id>/', CartItemDetailApiView.as_view(), name='api-cart-item-detail'),
    path('api/cart/clear/', CartClearApiView.as_view(), name='api-cart-clear'),
]
