from django.db import models
from django.conf import settings

from inventory.models import Product, RawMaterial

User = settings.AUTH_USER_MODEL



# CUSTOMERS 
class Customer(models.Model):
    """
    Represents both Leads and Customers.
    A Lead becomes a Customer when status = 'converted'
    """

    LEAD_STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('converted', 'Converted'),
        ('lost', 'Lost'),
    ]

    LEAD_SOURCE_CHOICES = [
        ('website', 'Website'),
        ('referral', 'Referral'),
        ('walkin', 'Walk-in'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    source = models.CharField(
        max_length=20,
        choices=LEAD_SOURCE_CHOICES,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=LEAD_STATUS_CHOICES,
        default='new'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_customer(self):
        return self.status == 'converted'

    def __str__(self):
        return self.name


# QUOTATIONS

class Quotation(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='quotations'
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    notes = models.TextField(blank=True)

    total_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    quotation_date = models.DateTimeField(auto_now_add=True)
    approval_date = models.DateTimeField(null=True, blank=True)

    def calculate_total(self):
        total = sum(item.total for item in self.items.all())
        self.total_price = total
        self.save(update_fields=['total_price'])

    def __str__(self):
        return f"Quotation #{self.pk}"


# QUOTATION ITEMS
class QuotationItem(models.Model):
    quotation = models.ForeignKey(
        Quotation,
        on_delete=models.CASCADE,
        related_name='items'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT
    )

    description = models.CharField(max_length=255, blank=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        editable=False
    )

    def save(self, *args, **kwargs):
        self.total = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"QuotationItem #{self.pk}"


# SALES ORDERS
class SalesOrder(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In-Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    quotation = models.ForeignKey(
        Quotation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='orders'
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    order_date = models.DateTimeField(auto_now_add=True)
    expected_delivery_date = models.DateField(null=True, blank=True)

    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"SalesOrder #{self.pk}"



# SALES ORDER ITEMS 
class SalesOrderItem(models.Model):
    """
    Locked raw materials copied from BOM / quotation
    Used for inventory deduction & production
    """

    order = models.ForeignKey(
        SalesOrder,
        on_delete=models.CASCADE,
        related_name='items'
    )

    material = models.ForeignKey(
        RawMaterial,
        on_delete=models.PROTECT
    )

    description = models.CharField(max_length=255, blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        editable=False
    )

    def save(self, *args, **kwargs):
        # Locked price & quantity once order is created
        self.total = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"OrderItem #{self.pk}"
