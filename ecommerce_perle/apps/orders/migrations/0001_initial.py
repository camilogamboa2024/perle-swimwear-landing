import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('catalog', '0001_initial'),
        ('customers', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=40, unique=True)),
                ('percentage', models.PositiveSmallIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Cart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_key', models.CharField(blank=True, db_index=True, max_length=50)),
                ('currency', models.CharField(default='COP', max_length=3)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('customer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='customers.customer')),
            ],
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('public_id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('session_key', models.CharField(blank=True, db_index=True, max_length=50)),
                ('status', models.CharField(choices=[('pending', 'Pendiente'), ('confirmed', 'Confirmado'), ('paid', 'Pagado'), ('cancelled', 'Cancelado')], db_index=True, default='pending', max_length=20)),
                ('payment_method', models.CharField(choices=[('whatsapp', 'WhatsApp'), ('manual', 'Manual'), ('wompi', 'Wompi'), ('stripe', 'Stripe')], default='whatsapp', max_length=20)),
                ('whatsapp_message', models.TextField(blank=True)),
                ('subtotal', models.PositiveIntegerField(default=0)),
                ('discount_total', models.PositiveIntegerField(default=0)),
                ('grand_total', models.PositiveIntegerField(default=0)),
                ('currency', models.CharField(default='COP', max_length=3)),
                ('paid_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('address', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='customers.address')),
                ('coupon', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='orders.coupon')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='customers.customer')),
            ],
            options={'indexes': [models.Index(fields=['status', 'created_at'], name='orders_orde_status_8ffe9c_idx')]},
        ),
        migrations.CreateModel(
            name='OrderStatusHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('from_status', models.CharField(blank=True, max_length=20)),
                ('to_status', models.CharField(max_length=20)),
                ('changed_at', models.DateTimeField(auto_now_add=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='status_history', to='orders.order')),
            ],
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField()),
                ('unit_price', models.PositiveIntegerField()),
                ('line_total', models.PositiveIntegerField()),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='orders.order')),
                ('variant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='catalog.productvariant')),
            ],
        ),
        migrations.CreateModel(
            name='CartItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('cart', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='orders.cart')),
                ('variant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='catalog.productvariant')),
            ],
            options={'unique_together': {('cart', 'variant')}},
        ),
    ]
