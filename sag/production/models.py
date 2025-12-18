from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import Q, Sum

from inventory.models import (
    RawMaterial,
    InventoryBatch,
    Warehouse,
    Product,
)
from sales.models import SalesOrder

User = settings.AUTH_USER_MODEL

# PRODUCTION STAGES

class ProductionStage(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    sequence_no = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sequence_no']
        indexes = [models.Index(fields=['sequence_no'])]
        verbose_name = "Production Stage"

    def __str__(self):
        return f"{self.sequence_no}. {self.name}"


# BILL OF MATERIALS

class BOM(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='boms')
    version_no = models.CharField(max_length=32, default='v1')
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('product', 'version_no')
        indexes = [models.Index(fields=['product', 'version_no'])]

    def __str__(self):
        return f"BOM {self.product} [{self.version_no}]"


class BOMItem(models.Model):
    bom = models.ForeignKey(BOM, on_delete=models.CASCADE, related_name='items')
    raw_material = models.ForeignKey(RawMaterial, on_delete=models.PROTECT)
    quantity_required = models.DecimalField(max_digits=12, decimal_places=3)
    unit = models.CharField(max_length=30, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(quantity_required__gt=0),
                name='bom_qty_positive'
            )
        ]

    def __str__(self):
        return f"{self.raw_material} x {self.quantity_required}"


# WORK ORDER

WO_STATUS = (
    ('planned', 'Planned'),
    ('in_progress', 'In Progress'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
)


class WorkOrder(models.Model):
    work_order_number = models.CharField(max_length=64, unique=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    sales_order = models.ForeignKey(
        SalesOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='work_orders'
    )
    quantity_to_produce = models.PositiveIntegerField()
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)

    status = models.CharField(
        max_length=20,
        choices=WO_STATUS,
        default='planned',
        db_index=True
    )

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workorders_created'
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['status', 'created_at'])]

    def __str__(self):
        return f"WO#{self.work_order_number} - {self.product}"

    def auto_complete_if_ready(self):
        if self.tasks.exists() and not self.tasks.exclude(status='completed').exists():
            self.status = 'completed'
            self.end_date = timezone.now().date()
            self.save(update_fields=['status', 'end_date'])

    def remaining_quantity(self):
        produced = self.outputs.aggregate(
            total=Sum('quantity_produced')
        )['total'] or 0
        return max(self.quantity_to_produce - produced, 0)


# PRODUCTION TASKS

TASK_STATUS = (
    ('pending', 'Pending'),
    ('in_progress', 'In Progress'),
    ('completed', 'Completed'),
)


class ProductionTask(models.Model):
    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name='tasks'
    )

    stage = models.ForeignKey(
        ProductionStage,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='production_tasks'
    )

    machine = models.CharField(max_length=120, blank=True)

    status = models.CharField(
        max_length=20,
        choices=TASK_STATUS,
        default='pending',
        db_index=True
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks_created'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['stage']),
        ]

    def start(self):
        if self.status != 'pending':
            return

        self.status = 'in_progress'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])

        if self.stage:
            ProductionStageLog.objects.update_or_create(
                work_order=self.work_order,
                stage=self.stage,
                defaults={
                    'status': 'running',
                    'started_at': timezone.now()
                }
            )

    def complete(self):
        if self.status == 'completed':
            return

        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])

        if self.stage:
            ProductionStageLog.objects.filter(
                work_order=self.work_order,
                stage=self.stage
            ).update(
                status='completed',
                completed_at=timezone.now()
            )

        self.work_order.auto_complete_if_ready()

    def __str__(self):
        return f"{self.title} ({self.status})"


# PRODUCTION STAGE LOG

LOG_STATUS = (
    ('running', 'Running'),
    ('completed', 'Completed'),
)


class ProductionStageLog(models.Model):
    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name='stage_logs'
    )
    stage = models.ForeignKey(ProductionStage, on_delete=models.PROTECT)

    status = models.CharField(max_length=16, choices=LOG_STATUS)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)

    class Meta:
        unique_together = ('work_order', 'stage')
        ordering = ['stage__sequence_no']


# RAW MATERIAL CONSUMPTION
class WorkOrderConsumption(models.Model):
    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name='consumptions'
    )
    raw_material = models.ForeignKey(RawMaterial, on_delete=models.PROTECT)

    batch = models.ForeignKey(
        InventoryBatch,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    quantity_used = models.DecimalField(max_digits=12, decimal_places=3)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(quantity_used__gt=0),
                name='consumed_qty_positive'
            )
        ]


# PRODUCTION OUTPUT

class ProductionOutput(models.Model):
    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name='outputs'
    )
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity_produced = models.PositiveIntegerField()
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)

    timestamp = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(quantity_produced__gt=0),
                name='output_qty_positive'
            )
        ]


class FinishedProductBatch(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    qty_available = models.PositiveIntegerField(default=0)
    produced_date = models.DateField(default=timezone.now)

    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='output_batches'
    )

    class Meta:
        ordering = ['-produced_date']


# PRODUCTION WASTAGE

class ProductionWastage(models.Model):
    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name='wastages'
    )
    raw_material = models.ForeignKey(RawMaterial, on_delete=models.PROTECT)
    quantity_wasted = models.DecimalField(max_digits=12, decimal_places=3)
    reason = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(quantity_wasted__gt=0),
                name='wastage_qty_positive'
            )
        ]
