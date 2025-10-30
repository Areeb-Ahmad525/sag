from django.db import models
from django.utils.translation import gettext_lazy as _

# --- Model 1: Supplier (Implicitly required by RawMaterials) ---
class Supplier(models.Model):
    """
    Represents the suppliers who provide the raw materials.
    Required as a foreign key target for RawMaterial.
    """
    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Suppliers"


# --- Model 2: Warehouses (warehouse_id, name, location) ---
class Warehouse(models.Model):
    """
    Represents the physical locations where inventory is stored.
    """
    # warehouse_id is handled automatically by Django's primary key 'id'
    name = models.CharField(max_length=100, unique=True, help_text=_("Name of the warehouse."))
    location = models.CharField(max_length=255, help_text=_("Physical address or location description."))

    def __str__(self):
        return f"{self.name} ({self.location[:30]}...)"


# --- Model 3: RawMaterials (material_id, type_name, ..., supplier_id) ---
class RawMaterial(models.Model):
    """
    Defines the properties of a raw material.
    """
    # material_id is handled automatically by Django's primary key 'id'

    TYPE_CHOICES = [
        ('AL', 'Aluminium'),
        ('GL', 'Glass'),
        ('SC', 'Screw'),
        ('GU', 'Glue'),
        ('RU', 'Rubber'),
        ('TO', 'Tools'),
    ]

    type_name = models.CharField(
        max_length=2,
        choices=TYPE_CHOICES,
        default='AL',
        help_text=_("The general type of the material (e.g., Aluminium, Glass).")
    )
    category = models.CharField(max_length=50, help_text=_("Category of the material (e.g., Metal Sheets, Adhesives)."))
    unit = models.CharField(max_length=10, help_text=_("Unit of measure (e.g., KG, PCS, M)."))
    size = models.CharField(max_length=50, blank=True, help_text=_("Dimensional size description (e.g., 4x8 ft)."))
    thickness = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text=_("Thickness in mm or another relevant unit."))
    colour = models.CharField(max_length=30, blank=True)

    # Stock-related fields
    current_stock = models.IntegerField(default=0, help_text=_("Total current quantity available across all batches/warehouses."))
    reorder_level = models.IntegerField(default=0, help_text=_("Minimum stock level before a reorder is triggered."))

    # Relationship: supplier_id (M:1 to Supplier)
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL, # If a supplier is deleted, material supplier is set to NULL
        null=True,
        blank=True,
        related_name='materials'
    )

    def __str__(self):
        return f"{self.get_type_name_display()} - {self.category}"

    class Meta:
        verbose_name_plural = "Raw Materials"
        ordering = ['type_name']


# --- Model 4: InventoryBatches (batch_id, material_id, warehouse_id, qty_available, received_date) ---
class InventoryBatch(models.Model):
    """
    Represents a specific batch of a raw material received on a certain date,
    stored at a particular warehouse.
    """
    # batch_id is handled automatically by Django's primary key 'id'

    # Relationship: material_id (M:1 to RawMaterial)
    material = models.ForeignKey(
        RawMaterial,
        on_delete=models.CASCADE, # If material is deleted, delete its batches
        related_name='batches'
    )

    # Relationship: warehouse_id (M:1 to Warehouse)
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT, # Prevent deleting warehouse if batches exist there
        related_name='inventory_batches'
    )

    qty_available = models.IntegerField(default=0)
    received_date = models.DateField()

    def __str__(self):
        return f"Batch {self.pk} of {self.material.type_name} @ {self.warehouse.name}"

    class Meta:
        verbose_name_plural = "Inventory Batches"
        ordering = ['-received_date']


# --- Model 5: StockMovements (movement_id, batch_id, from_where, to_where, qty, movement_type, created_at) ---
class StockMovement(models.Model):
    """
    Records the movement of stock, such as receiving, consumption, or transfer.
    """
    # movement_id is handled automatically by Django's primary key 'id'

    MOVEMENT_CHOICES = [
        ('IN', 'Stock In (Receive)'),
        ('OUT', 'Stock Out (Consumption/Sale)'),
        ('TR', 'Transfer'),
        ('ADJ', 'Adjustment'),
    ]

    # Relationship: batch_id (M:1 to InventoryBatch)
    batch = models.ForeignKey(
        InventoryBatch,
        on_delete=models.PROTECT, # Prevent deleting a batch that has movement records
        related_name='movements'
    )

    # In a real system, 'from_where' and 'to_where' should link to Warehouse or be Nullable
    # We use ForeignKey to Warehouse for structural integrity.
    from_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name='outgoing_movements',
        null=True, # Allow null for 'IN' movements (receiving new stock)
        blank=True,
        help_text=_("Source warehouse for the movement. Null if stock is newly received.")
    )

    to_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name='incoming_movements',
        null=True, # Allow null for 'OUT' movements (consumption/sale)
        blank=True,
        help_text=_("Destination warehouse for the movement. Null if stock is consumed.")
    )

    qty = models.IntegerField(help_text=_("Quantity moved."))
    
    movement_type = models.CharField(
        max_length=3,
        choices=MOVEMENT_CHOICES,
        help_text=_("Type of movement (e.g., IN, OUT, Transfer).")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.movement_type} {self.qty} units of Batch {self.batch.pk}"

    class Meta:
        verbose_name_plural = "Stock Movements"
        ordering = ['-created_at']
