from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='InventoryMovement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('movement_type', models.CharField(choices=[('IN', 'Ingreso'), ('OUT', 'Salida'), ('ADJUST', 'Ajuste')], max_length=10)),
                ('quantity', models.IntegerField()),
                ('reason', models.CharField(max_length=180)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('variant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='movements', to='catalog.productvariant')),
            ],
            options={'indexes': [models.Index(fields=['variant', 'created_at'], name='inventory_i_variant_56b574_idx')]},
        ),
        migrations.CreateModel(
            name='StockLevel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('available', models.IntegerField(default=0)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('variant', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='stock_level', to='catalog.productvariant')),
            ],
            options={'indexes': [models.Index(fields=['available'], name='inventory_s_availab_7b9ddc_idx')]},
        ),
    ]
