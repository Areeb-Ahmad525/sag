from django.db import models
from django.conf import settings
from django.utils import timezone
from inventory.models import Supplier, RawMaterial, Warehouse, InventoryBatch, StockMovement

User = settings.AUTH_USER_MODEL

# --- Purchase Request (PR) ---
class PurchaseRequest(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='purchase_requests')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    required_by = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    def __str__(self):
        return f"PR#{self.pk} - {self.title} ({self.get_status_display()})"


class PurchaseRequestItem(models.Model):
    pr = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name='items')
    material = models.ForeignKey(RawMaterial, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    unit = models.CharField(max_length=20, blank=True)
    notes = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.material} x {self.quantity}"


# --- Purchase Order (PO) ---
class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('confirmed', 'Confirmed'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ]

    po_number = models.CharField(max_length=50, unique=True)
    created_from_pr = models.ForeignKey(PurchaseRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='generated_pos')
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='purchase_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    expected_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"PO {self.po_number} - {self.supplier.name} ({self.get_status_display()})"


class PurchaseOrderItem(models.Model):
    po = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    material = models.ForeignKey(RawMaterial, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    received_quantity = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.material} x {self.quantity} ({self.po.po_number})"


# --- Goods Received Note (GRN) ---
class GoodsReceived(models.Model):
    STATUS_CHOICES = [
        ('received', 'Received'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected'),
    ]

    grn_number = models.CharField(max_length=50, unique=True)
    po = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='grns')
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='grns')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"GRN {self.grn_number} - {self.supplier.name} ({self.get_status_display()})"


class GoodsReceivedItem(models.Model):
    grn = models.ForeignKey(GoodsReceived, on_delete=models.CASCADE, related_name='items')
    po_item = models.ForeignKey(PurchaseOrderItem, on_delete=models.SET_NULL, null=True, blank=True)
    material = models.ForeignKey(RawMaterial, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    batch_reference = models.CharField(max_length=100, blank=True)  # optional reference

    def __str__(self):
        return f"{self.material} x {self.quantity} (GRN {self.grn.grn_number})"
