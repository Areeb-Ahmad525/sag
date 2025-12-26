# production/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class ProductionOrder(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),                         #  NEW (hidden everywhere)
        ('waiting_inventory', 'Waiting for Inventory'),  #  visible in inventory
        ('ready', 'Ready for Production'),
        ('in_progress', 'In Progress'),
        ('waiting_qc', 'Waiting for Quality Check'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
    ]

    sales_order = models.OneToOneField(
        'sales.SalesOrder',
        on_delete=models.CASCADE,
        related_name='production'
    )

    manager = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='production_orders'
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='draft'   #  IMPORTANT CHANGE
    )

    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # -------------------------------
    # STATUS HELPERS (OPTIONAL BUT CLEAN)
    # -------------------------------
    def request_inventory(self):
        if self.status == 'draft':
            self.status = 'waiting_inventory'
            self.save()

    def mark_ready(self):
        if self.status == 'waiting_inventory':
            self.status = 'ready'
            self.save()

    def start_production(self):
        if self.status == 'ready':
            self.status = 'in_progress'
            self.started_at = timezone.now()
            self.save()

    def mark_completed(self):
        if self.status == 'waiting_qc':
            self.status = 'completed'
            self.completed_at = timezone.now()
            self.save()

    def __str__(self):
        return f"ProductionOrder for SO #{self.sales_order_id}"




class MaterialRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('onhold', 'OnHold'),
    ]

    production_order = models.OneToOneField(
        ProductionOrder,
        on_delete=models.CASCADE,
        related_name='material_request'
    )

    requested_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='material_requests'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    remarks = models.TextField(blank=True)

    requested_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    def approve(self):
        self.status = 'approved'
        self.responded_at = timezone.now()
        self.save()

        self.production_order.status = 'ready'
        self.production_order.save()

    def __str__(self):
        return f"MaterialRequest #{self.pk}"




class MaterialRequestItem(models.Model):
    material_name = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit = models.CharField(max_length=50)

    material_request = models.ForeignKey(
        MaterialRequest,
        on_delete=models.CASCADE,
        related_name='items'
    )

    def __str__(self):
        return f"{self.material_name} ({self.quantity} {self.unit})"
    
    
    
    

class ProductionTask(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('blocked', 'Blocked'),
    ]

    production_order = models.ForeignKey(
        ProductionOrder,
        on_delete=models.CASCADE,
        related_name='tasks'
    )

    name = models.CharField(max_length=200)

    assigned_to = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='assigned_tasks'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    remarks = models.TextField(blank=True)

    # 🔴 ADD THIS LINE
    started_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def mark_completed(self):
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.name} - PO #{self.production_order_id}"
