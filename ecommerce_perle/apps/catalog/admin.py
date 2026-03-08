from decimal import Decimal

from django.contrib import admin
from django import forms
from django.db.models import Min
from django.utils.html import format_html

from apps.orders.money import cents_to_usd_decimal, format_usd, usd_to_cents

from .models import Category, Product, ProductImage, ProductVariant


class ProductVariantPricingForm(forms.ModelForm):
    price_usd = forms.DecimalField(
        label='Precio (USD)',
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.00'),
    )
    compare_at_price_usd = forms.DecimalField(
        label='Precio de referencia (USD)',
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.00'),
        required=False,
    )

    class Meta:
        model = ProductVariant
        exclude = ('price_usd_cents', 'compare_at_price_usd_cents')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = self.instance
        if not instance or not instance.pk:
            return
        self.fields['price_usd'].initial = cents_to_usd_decimal(instance.price_usd_cents)
        if instance.compare_at_price_usd_cents is not None:
            self.fields['compare_at_price_usd'].initial = cents_to_usd_decimal(instance.compare_at_price_usd_cents)

    def clean(self):
        cleaned_data = super().clean()
        price_usd = cleaned_data.get('price_usd')
        compare_at_price_usd = cleaned_data.get('compare_at_price_usd')
        cleaned_data['price_usd_cents'] = usd_to_cents(price_usd)
        cleaned_data['compare_at_price_usd_cents'] = (
            usd_to_cents(compare_at_price_usd) if compare_at_price_usd is not None else None
        )
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.price_usd_cents = self.cleaned_data['price_usd_cents']
        instance.compare_at_price_usd_cents = self.cleaned_data['compare_at_price_usd_cents']
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    form = ProductVariantPricingForm
    extra = 0
    fields = ('sku', 'size', 'color', 'price_usd', 'compare_at_price_usd', 'is_default', 'is_active', 'stock_preview')
    readonly_fields = ('stock_preview',)
    classes = ('collapse',)

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
    list_display = (
        'cover_preview',
        'name',
        'category',
        'active_badge',
        'variant_count',
        'from_price',
        'created_at',
    )
    list_filter = ('is_active', 'category', 'created_at')
    search_fields = ('name', 'slug')
    list_select_related = ('category',)
    inlines = [ProductVariantInline, ProductImageInline]
    fieldsets = (
        (
            'Identidad del producto',
            {
                'fields': (
                    'name',
                    'slug',
                    'category',
                    'is_active',
                )
            },
        ),
        (
            'Contenido',
            {
                'fields': ('description',),
            },
        ),
    )

    @admin.display(description='Portada')
    def cover_preview(self, obj):
        first = obj.images.first()
        if not first or not first.image_url:
            return '-'
        return format_html(
            '<img src="{}" alt="{}" style="width:42px;height:52px;border-radius:8px;object-fit:cover;border:1px solid #d4d6da;" />',
            first.image_url,
            first.alt_text or obj.name,
        )

    @admin.display(description='Estado')
    def active_badge(self, obj):
        if obj.is_active:
            return format_html('<span class="perle-pill perle-pill-success">Activo</span>')
        return format_html('<span class="perle-pill perle-pill-danger">Inactivo</span>')

    @admin.display(description='Variantes')
    def variant_count(self, obj):
        return obj.variants.count()

    @admin.display(description='Desde (USD)')
    def from_price(self, obj):
        cents = obj.variants.aggregate(v=Min('price_usd_cents')).get('v') or 0
        return format_usd(cents)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('category').prefetch_related('images', 'variants')


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    form = ProductVariantPricingForm
    list_display = (
        'sku',
        'product',
        'size',
        'color',
        'price_display',
        'stock_available',
        'active_badge',
        'is_default',
    )
    list_filter = ('is_active', 'is_default', 'size', 'color')
    search_fields = ('sku', 'product__name')
    list_select_related = ('product',)
    fieldsets = (
        (
            'Identidad',
            {
                'fields': ('product', 'sku'),
            },
        ),
        (
            'Comercial',
            {
                'fields': ('size', 'color', 'price_usd', 'compare_at_price_usd'),
            },
        ),
        (
            'Publicación',
            {
                'fields': ('is_active', 'is_default'),
            },
        ),
    )

    @admin.display(description='Stock')
    def stock_available(self, obj):
        try:
            return obj.stock_level.available
        except ProductVariant.stock_level.RelatedObjectDoesNotExist:
            return 'Sin stock'

    @admin.display(ordering='price_usd_cents', description='Precio')
    def price_display(self, obj):
        return format_usd(obj.price_usd_cents)

    @admin.display(description='Estado')
    def active_badge(self, obj):
        if obj.is_active:
            return format_html('<span class="perle-pill perle-pill-success">Activo</span>')
        return format_html('<span class="perle-pill perle-pill-danger">Inactivo</span>')


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
    list_display = ('name', 'slug', 'products_count')
    search_fields = ('name', 'slug')

    @admin.display(description='Productos')
    def products_count(self, obj):
        return obj.products.count()
