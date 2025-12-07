# inventory/models.py
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings

# local import for typing only; avoids circular import in runtime
User = settings.AUTH_USER_MODEL


# NEW MODEL — FINISHED GOODS PRODUCT TABLE
class Product(models.Model):
    """
    Finished Goods Table
    Used by Production module (BOM, Work Orders, Outputs)
    """
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=100, blank=True)
    size = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=30, blank=True)
    unit = models.CharField(max_length=10, default="pcs")

    # Optional: link preferred warehouse
    default_warehouse = models.ForeignKey(
        'Warehouse',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Finished Products"
        ordering = ['name']


# Existing Supplier Table (unchanged)
class Supplier(models.Model):
    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Suppliers"


# Warehouse Table (unchanged)
class Warehouse(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text=_("Name of the warehouse."))
    location = models.CharField(max_length=255, help_text=_("Physical address or location description."))

    def __str__(self):
        return f"{self.name} ({self.location[:30]}...)"

    class Meta:
        verbose_name_plural = "Warehouses"


# Raw Material Table (unchanged logic)
class RawMaterial(models.Model):
    TYPE_CHOICES = [
        ('AL', 'Aluminium'),
        ('GL', 'Glass'),
        ('SC', 'Screw'),
        ('GU', 'Glue'),
        ('RU', 'Rubber'),
        ('TO', 'Tools'),
    ]

    type_name = models.CharField(max_length=2, choices=TYPE_CHOICES, default='AL')
    category = models.CharField(max_length=50)
    unit = models.CharField(max_length=10)
    size = models.CharField(max_length=50, blank=True)
    thickness = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    colour = models.CharField(max_length=30, blank=True)

    current_stock = models.IntegerField(default=0)
    reorder_level = models.IntegerField(default=0)

    supplier = models.ForeignKey(
        Supplier, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='materials'
    )

    def __str__(self):
        return f"{self.get_type_name_display()} - {self.category}"

    class Meta:
        verbose_name_plural = "Raw Materials"
        ordering = ['type_name']

    def recalc_current_stock(self):
        """
        Recalculate current_stock from sum of batch qty_available.
        """
        total = self.batches.aggregate(total=models.Sum('qty_available'))['total'] or 0
        self.current_stock = int(total)
        self.save(update_fields=['current_stock'])


# -----------------------------------------
# Inventory Batch (unchanged)
# -----------------------------------------
class InventoryBatch(models.Model):
    material = models.ForeignKey(RawMaterial, on_delete=models.CASCADE, related_name='batches')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='inventory_batches')
    qty_available = models.IntegerField(default=0)
    received_date = models.DateField()

    def __str__(self):
        return f"Batch {self.pk} of {self.material.get_type_name_display()} @ {self.warehouse.name}"

    class Meta:
        verbose_name_plural = "Inventory Batches"
        ordering = ['-received_date']


# -----------------------------------------
# Stock Movement (unchanged logic — only comments added)
# -----------------------------------------
class StockMovement(models.Model):
    MOVEMENT_CHOICES = [
        ('IN', 'Stock In (Receive)'),
        ('OUT', 'Stock Out (Consumption/Sale)'),
        ('TR', 'Transfer'),
        ('ADJ', 'Adjustment'),
    ]

    batch = models.ForeignKey(InventoryBatch, on_delete=models.PROTECT, related_name='movements')
    from_warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='outgoing_movements', null=True, blank=True)
    to_warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='incoming_movements', null=True, blank=True)
    qty = models.IntegerField()
    movement_type = models.CharField(max_length=3, choices=MOVEMENT_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    # internal flag to prevent double-processing when saving programmatically
    _processed = False

    def __str__(self):
        return f"{self.movement_type} {self.qty} units of Batch {self.batch.pk}"

    class Meta:
        verbose_name_plural = "Stock Movements"
        ordering = ['-created_at']

    def process_movement(self):
        """
        Apply the movement to batches and recalc RawMaterial.current_stock.
        This function should be called inside a DB transaction.
        """
        if self._processed:
            return

        if self.qty <= 0:
            raise ValueError("Quantity must be positive")

        material = self.batch.material

        if self.movement_type == 'IN':
            self.batch.qty_available = models.F('qty_available') + self.qty
            self.batch.save(update_fields=['qty_available'])

        elif self.movement_type == 'OUT':
            self.batch.refresh_from_db()
            if self.qty > self.batch.qty_available:
                raise ValueError("Not enough stock in selected batch for OUT movement.")
            self.batch.qty_available = models.F('qty_available') - self.qty
            self.batch.save(update_fields=['qty_available'])

        elif self.movement_type == 'TR':
            self.batch.refresh_from_db()
            if not self.from_warehouse or not self.to_warehouse:
                raise ValueError("Transfer requires both from_warehouse and to_warehouse.")
            if self.from_warehouse != self.batch.warehouse:
                raise ValueError("Selected batch does not belong to the from_warehouse.")
            if self.qty > self.batch.qty_available:
                raise ValueError("Not enough stock for transfer.")

            self.batch.qty_available = models.F('qty_available') - self.qty
            self.batch.save(update_fields=['qty_available'])

            dest_batch = InventoryBatch.objects.filter(
                material=material,
                warehouse=self.to_warehouse
            ).order_by('-received_date').first()

            if dest_batch:
                dest_batch.qty_available = models.F('qty_available') + self.qty
                dest_batch.save(update_fields=['qty_available'])
            else:
                InventoryBatch.objects.create(
                    material=material,
                    warehouse=self.to_warehouse,
                    qty_available=self.qty,
                    received_date=timezone.now().date()
                )

        elif self.movement_type == 'ADJ':
            self.batch.refresh_from_db()
            new_qty = self.batch.qty_available + self.qty
            if new_qty < 0:
                raise ValueError("Adjustment results in negative stock.")
            self.batch.qty_available = models.F('qty_available') + self.qty
            self.batch.save(update_fields=['qty_available'])
        else:
            raise ValueError("Unknown movement type")

        material.recalc_current_stock()
        self._processed = True

    def save(self, *args, **kwargs):
        """
        Override save to process stock changes on create.
        Use transaction.atomic to ensure consistency.
        """
        is_new = self.pk is None
        with transaction.atomic():
            super().save(*args, **kwargs)
            if is_new:
                self.process_movement()
