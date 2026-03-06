"""
Django signals for SK Cafe.

Connected signals:
- ``post_save`` on ``KitchenOrder`` → set ``estimated_minutes`` from item count.
- ``post_save`` on ``KitchenOrder`` (completed) → mark the related Table as available.
- ``post_delete`` on ``TableSession`` → mark the related Table as available.
"""

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver


@receiver(post_save, sender='cafe.KitchenOrder')
def kitchen_order_post_save(sender, instance, created, **kwargs):
    """
    After a KitchenOrder is saved:

    * If newly created, estimate preparation time based on item count
      (3 minutes per item, minimum 5, maximum 45).
    * If status changes to 'completed', try to mark the corresponding
      Table as available (best-effort; Table row may not exist yet).
    """
    if created:
        item_count = instance.order_items.count()
        estimated = max(5, min(item_count * 3, 45))
        # Use queryset update to avoid re-triggering the signal
        sender.objects.filter(pk=instance.pk).update(estimated_minutes=estimated)
        return

    if instance.status == 'completed':
        _try_mark_table_available(instance.table_num)


@receiver(post_delete, sender='cafe.TableSession')
def table_session_post_delete(sender, instance, **kwargs):
    """When a TableSession is deleted (session closed), mark the Table as available."""
    _try_mark_table_available(instance.table_num)


def _try_mark_table_available(table_num: int) -> None:
    """Set ``Table.status = 'available'`` for *table_num* if a row exists."""
    try:
        from cafe.models import Table  # local import to avoid app-registry issues
        Table.objects.filter(number=table_num).update(status=Table.STATUS_AVAILABLE)
    except Exception:
        pass
