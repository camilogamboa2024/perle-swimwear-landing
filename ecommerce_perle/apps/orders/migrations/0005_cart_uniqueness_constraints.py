from django.db import migrations, models


def _merge_cart_items(*, cart_item_model, source_cart_id, target_cart_id):
    source_items = cart_item_model.objects.filter(cart_id=source_cart_id).order_by('id')
    for source_item in source_items:
        existing = cart_item_model.objects.filter(
            cart_id=target_cart_id,
            variant_id=source_item.variant_id,
        ).first()
        if existing:
            existing.quantity += source_item.quantity
            existing.save(update_fields=['quantity'])
            source_item.delete()
            continue
        source_item.cart_id = target_cart_id
        source_item.save(update_fields=['cart'])


def deduplicate_carts_before_constraints(apps, schema_editor):
    Cart = apps.get_model('orders', 'Cart')
    CartItem = apps.get_model('orders', 'CartItem')

    # 1) Deduplicate by customer (authenticated carts)
    duplicated_customer_ids = (
        Cart.objects.exclude(customer_id__isnull=True)
        .values_list('customer_id', flat=True)
        .distinct()
    )
    for customer_id in duplicated_customer_ids:
        carts = list(
            Cart.objects.filter(customer_id=customer_id)
            .order_by('created_at', 'id')
        )
        if len(carts) < 2:
            continue
        keep_cart = carts[0]
        for duplicate_cart in carts[1:]:
            _merge_cart_items(
                cart_item_model=CartItem,
                source_cart_id=duplicate_cart.id,
                target_cart_id=keep_cart.id,
            )
            duplicate_cart.delete()

    # 2) Deduplicate by session key (guest carts)
    duplicated_session_keys = (
        Cart.objects.exclude(session_key='')
        .values_list('session_key', flat=True)
        .distinct()
    )
    for session_key in duplicated_session_keys:
        carts = list(
            Cart.objects.filter(session_key=session_key)
            .order_by('created_at', 'id')
        )
        if len(carts) < 2:
            continue

        keep_cart = carts[0]
        for duplicate_cart in carts[1:]:
            conflicting_customers = (
                keep_cart.customer_id
                and duplicate_cart.customer_id
                and keep_cart.customer_id != duplicate_cart.customer_id
            )
            if conflicting_customers:
                duplicate_cart.session_key = ''
                duplicate_cart.save(update_fields=['session_key'])
                continue

            if keep_cart.customer_id is None and duplicate_cart.customer_id is not None:
                keep_cart.customer_id = duplicate_cart.customer_id
                keep_cart.save(update_fields=['customer'])

            _merge_cart_items(
                cart_item_model=CartItem,
                source_cart_id=duplicate_cart.id,
                target_cart_id=keep_cart.id,
            )
            duplicate_cart.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_alter_cart_options_alter_cartitem_options_and_more'),
    ]

    operations = [
        migrations.RunPython(deduplicate_carts_before_constraints, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='cart',
            constraint=models.UniqueConstraint(
                fields=('customer',),
                condition=models.Q(customer__isnull=False),
                name='orders_cart_unique_customer_not_null',
            ),
        ),
        migrations.AddConstraint(
            model_name='cart',
            constraint=models.UniqueConstraint(
                fields=('session_key',),
                condition=~models.Q(session_key=''),
                name='orders_cart_unique_session_key_not_blank',
            ),
        ),
    ]
