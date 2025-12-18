from django.db import models, transaction
from django.conf import settings
from django.utils import timezone

# Import inventory models
from inventory.models import RawMaterial, InventoryBatch, Warehouse,Product

User = settings.AUTH_USER_MODEL

# --- ProductionStage ---
class ProductionStage(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    sequence_no = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sequence_no']
        verbose_name = "Production Stage"

    def __str__(self):
        return f"{self.sequence_no} - {self.name}"

# --- Product (finished good) ---
class Product(models.Model):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=80, blank=True, null=True)
    category = models.CharField(max_length=100, blank=True)
    size = models.CharField(max_length=80, blank=True)
    color = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Product"
        ordering = ['name']

    def __str__(self):
        return self.name

# --- BOM ---
class BOM(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='boms')
    version_no = models.CharField(max_length=32, default='v1')
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Bill of Materials"
        ordering = ['-created_at']

    def __str__(self):
        return f"BOM {self.product} [{self.version_no}]"

class BOMItem(models.Model):
    bom = models.ForeignKey(BOM, on_delete=models.CASCADE, related_name='items')
    raw_material = models.ForeignKey(RawMaterial, on_delete=models.PROTECT)
    quantity_required = models.DecimalField(max_digits=12, decimal_places=3)  # units same as RawMaterial.unit
    unit = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return f"{self.bom} - {self.raw_material} x {self.quantity_required}"

# --- WorkOrder ---
WO_STATUS = (
    ('planned','Planned'),
    ('in_progress','In-Progress'),
    ('completed','Completed'),
    ('cancelled','Cancelled'),
)

class WorkOrder(models.Model):
    work_order_number = models.CharField(max_length=64, unique=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    # Optional link to a SalesOrder (created in the sales app)
    sales_order = models.ForeignKey(
        'sales.SalesOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='work_orders',
        help_text='Linked sales order, if this WO was created to fulfil a sales order'
    )
    quantity_to_produce = models.PositiveIntegerField()
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, help_text="Where finished goods will be stored")
    status = models.CharField(max_length=24, choices=WO_STATUS, default='planned')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='workorders_created')
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"WO#{self.work_order_number} - {self.product} x {self.quantity_to_produce}"

# --- WorkOrderConsumption ---
class WorkOrderConsumption(models.Model):
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='consumptions')
    raw_material = models.ForeignKey(RawMaterial, on_delete=models.PROTECT)
    batch = models.ForeignKey(InventoryBatch, on_delete=models.PROTECT, null=True, blank=True,
                              help_text="Batch used (FIFO selection recommended)")
    quantity_used = models.DecimalField(max_digits=12, decimal_places=3)
    timestamp = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.work_order} consumed {self.quantity_used} {self.raw_material}"

# --- ProductionOutput (finished goods) ---
class FinishedProductBatch(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='batches')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='product_batches')
    qty_available = models.IntegerField(default=0)
    produced_date = models.DateField(default=timezone.now)
    work_order = models.ForeignKey(WorkOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='output_batches')

    class Meta:
        verbose_name = "Finished Product Batch"
        ordering = ['-produced_date']

    def __str__(self):
        return f"FP Batch#{self.pk} {self.product} @ {self.warehouse.name}"

class ProductionOutput(models.Model):
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='outputs')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity_produced = models.PositiveIntegerField()
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    timestamp = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Output WO#{self.work_order.work_order_number} -> {self.quantity_produced} {self.product}"

# --- ProductionWastage ---
class ProductionWastage(models.Model):
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='wastages')
    raw_material = models.ForeignKey(RawMaterial, on_delete=models.PROTECT)
    quantity_wasted = models.DecimalField(max_digits=12, decimal_places=3)
    reason = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Waste WO#{self.work_order.work_order_number} - {self.raw_material} {self.quantity_wasted}"

# --- ProductionStageLog ---
LOG_STATUS = (
    ('pending','Pending'),
    ('running','Running'),
    ('completed','Completed'),
)
class ProductionStageLog(models.Model):
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='stage_logs')
    stage = models.ForeignKey(ProductionStage, on_delete=models.PROTECT)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=LOG_STATUS, default='pending')
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.work_order} - {self.stage.name} ({self.status})"
