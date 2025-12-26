from django.db.models.signals import post_save
from django.dispatch import receiver
from sales.models import SalesOrder
from production.models import ProductionOrder


@receiver(post_save, sender=SalesOrder)
def create_production_order(sender, instance, **kwargs):
    if instance.status == 'in_progress':
        ProductionOrder.objects.get_or_create(
            sales_order=instance,
            defaults={
                'manager': instance.assigned_to
            }
        )
