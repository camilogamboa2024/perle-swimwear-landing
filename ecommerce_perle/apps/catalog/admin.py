from django.contrib import admin
from django.db.models import Min
from django.utils.html import format_html

from .models import Category, Product, ProductImage, ProductVariant


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = ('sku', 'size', 'color', 'price_cop', 'compare_at_price_cop', 'is_default', 'is_active', 'stock_preview')
    readonly_fields = ('stock_preview',)

    @admin.display(description='Stock')
    def stock_preview(self, obj):
        if not obj.pk:
            return '-'
        try:
            return obj.stock_level.available
        except ProductVariant.stock_level.RelatedObjectDoesNotExist:
            return 'Sin stock'


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    fields = ('image_url', 'alt_text', 'sort_order', 'thumbnail')
    readonly_fields = ('thumbnail',)

    @admin.display(description='Preview')
    def thumbnail(self, obj):
        if not obj.image_url:
            return '-'
        return format_html(
            '<img src="{}" alt="{}" style="width:52px;height:52px;border-radius:8px;object-fit:cover;border:1px solid #d4d6da;" />',
            obj.image_url,
            obj.alt_text or 'preview',
        )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_active', 'variant_count', 'from_price', 'created_at')
    list_filter = ('is_active', 'category', 'created_at')
    search_fields = ('name', 'slug')
    inlines = [ProductVariantInline, ProductImageInline]

    @admin.display(description='Variantes')
    def variant_count(self, obj):
        return obj.variants.count()

    @admin.display(description='Desde (COP)')
    def from_price(self, obj):
        return obj.variants.aggregate(v=Min('price_cop')).get('v') or 0


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('sku', 'product', 'size', 'color', 'price_cop', 'is_active', 'is_default')
    list_filter = ('is_active', 'is_default', 'size', 'color')
    search_fields = ('sku', 'product__name')


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'sort_order', 'thumbnail')
    search_fields = ('product__name', 'alt_text')
    ordering = ('product', 'sort_order')

    @admin.display(description='Preview')
    def thumbnail(self, obj):
        if not obj.image_url:
            return '-'
        return format_html(
            '<img src="{}" alt="{}" style="width:42px;height:42px;border-radius:6px;object-fit:cover;border:1px solid #d4d6da;" />',
            obj.image_url,
            obj.alt_text or 'preview',
        )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')
