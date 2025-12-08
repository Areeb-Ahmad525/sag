from django.contrib import admin
from .models import (
    Supplier,
    Warehouse,
    RawMaterial,
    InventoryBatch,
    StockMovement,
    Product
)

# --- 1. Supplier Admin ---
@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    """Admin configuration for the Supplier model."""
    list_display = ('name', 'contact_person', 'email', 'phone_number')
    search_fields = ('name', 'email')
    ordering = ('name',)

# --- 2. Warehouse Admin ---
@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    """Admin configuration for the Warehouse model."""
    list_display = ('name', 'location')
    search_fields = ('name', 'location')

# --- 3. RawMaterial Admin ---
@admin.register(RawMaterial)
class RawMaterialAdmin(admin.ModelAdmin):
    """Admin configuration for the RawMaterial model."""
    # current_stock is read-only as it should be managed by the system
    list_display = ('get_type_name_display', 'category', 'current_stock', 'unit', 'reorder_level', 'supplier')
    list_filter = ('category', 'supplier')
    search_fields = ('type_name',)
    # Makes 'current_stock' visible but prevents manual editing
    readonly_fields = ('current_stock',)


# --- 4. InventoryBatch Admin ---
@admin.register(InventoryBatch)
class InventoryBatchAdmin(admin.ModelAdmin):
    """Admin configuration for the InventoryBatch model."""
    # FIX: Use 'id' (Django's default PK) instead of 'batch_id'
    list_display = ('id', 'material', 'warehouse', 'qty_available', 'received_date')
    list_filter = ('warehouse', 'received_date')
    search_fields = ('material__type_name',)
    # FIX: Use 'id' instead of 'batch_id'
    readonly_fields = ('id',)
    date_hierarchy = 'received_date'

# --- 5. StockMovement Admin ---
@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    """Admin configuration for the StockMovement model."""
    # FIX: Use 'id' (Django's default PK) instead of 'movement_id'
    list_display = ('id', 'batch', 'movement_type', 'qty', 'from_warehouse', 'to_warehouse', 'created_at')
    list_filter = ('movement_type', 'created_at', 'from_warehouse', 'to_warehouse')
    search_fields = ('batch__material__type_name',)
    date_hierarchy = 'created_at'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "size", "color")
    search_fields = ("name", "category")