# procurement/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# import Supplier, RawMaterial, Warehouse from inventory app
# use app-label string or direct import (direct import preferred here)
from inventory.models import Supplier, RawMaterial, Warehouse

PR_STATUS = (
    ('draft', 'Draft'),
    ('submitted', 'Submitted'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
)

PO_STATUS = (
    ('draft', 'Draft'),
    ('sent', 'Sent'),
    ('confirmed', 'Confirmed'),
    ('cancelled', 'Cancelled'),
)

GRN_STATUS = (
    ('received', 'Received'),
    ('confirmed', 'Confirmed'),
    ('cancelled', 'Cancelled'),
)


class PurchaseRequest(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='prs_created')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=PR_STATUS, default='draft')

    def __str__(self):
        return f"PR#{self.pk} - {self.title}"


class PurchaseRequestItem(models.Model):
    pr = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name='items')
    material = models.ForeignKey(RawMaterial, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    requested_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"PR#{self.pr.pk} - {self.material} x {self.quantity}"


class PurchaseOrder(models.Model):
    po_number = models.CharField(max_length=64, blank=True, null=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchase_orders')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='pos_created')
    created_at = models.DateTimeField(auto_now_add=True)
    expected_delivery = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=PO_STATUS, default='draft')
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"PO#{self.pk} - {self.supplier.name}"


class PurchaseOrderItem(models.Model):
    po = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    material = models.ForeignKey(RawMaterial, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    received_quantity = models.PositiveIntegerField(default=0)  # updated when GRN confirmed
    notes = models.TextField(blank=True)

    def line_total(self):
        if self.unit_price:
            return self.unit_price * self.quantity
        return None

    def __str__(self):
        return f"PO#{self.po.pk} - {self.material} x {self.quantity}"


class GoodsReceived(models.Model):
    grn_number = models.CharField(max_length=64, blank=True, null=True)
    po = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='grns')
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='grns')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='grns')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='grns_created')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=GRN_STATUS, default='received')
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"GRN#{self.pk} - {self.supplier.name}"


class GoodsReceivedItem(models.Model):
    grn = models.ForeignKey(GoodsReceived, on_delete=models.CASCADE, related_name='items')
    material = models.ForeignKey(RawMaterial, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    po_item = models.ForeignKey(PurchaseOrderItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='grn_items')
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"GRN#{self.grn.pk} - {self.material} x {self.quantity}"
