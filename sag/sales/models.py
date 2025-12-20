from decimal import Decimal
from django.db import models
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

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
        blank='website'
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


# QUOTATIONS (PRE-SALES)
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

    # Calculated field (never manual)
    total_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        editable=False
    )

    quotation_date = models.DateTimeField(auto_now_add=True)
    approval_date = models.DateTimeField(null=True, blank=True)

    # BUSINESS LOGIC
    def recalculate_total(self):
        """
        Recalculate quotation total from its items.
        """
        total = sum(
            (item.total for item in self.items.all()),
            Decimal('0.00')
        )
        self.total_price = total
        self.save(update_fields=['total_price'])

    def approve(self):
        """
        Approve quotation manually.
        """
        if self.status != 'sent':
            raise ValueError("Only sent quotations can be approved.")

        self.status = 'approved'
        self.approval_date = timezone.now()
        self.save(update_fields=['status', 'approval_date'])

    def __str__(self):
        return f"Quotation #{self.pk} - {self.customer}"

# QUOTATION ITEMS
class QuotationItem(models.Model):
    quotation = models.ForeignKey(
        Quotation,
        on_delete=models.CASCADE,
        related_name='items'
    )

    product_name = models.CharField(
        max_length=200,
        help_text="Enter item  (e.g. Door, Window)"
    )

    description = models.CharField(
        max_length=255,
        blank=True
    )

    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        editable=False
    )

    # BUSINESS LOGIC
    def save(self, *args, **kwargs):
        # calculate item total
        self.total = Decimal(self.quantity) * self.unit_price
        super().save(*args, **kwargs)

        # keep quotation total in sync
        if self.quotation_id:
            self.quotation.recalculate_total()

    def delete(self, *args, **kwargs):
        quotation = self.quotation
        super().delete(*args, **kwargs)
        quotation.recalculate_total()

    def __str__(self):
        return f"{self.product_name} × {self.quantity}"

# SALES ORDERS (POST-CONFIRMATION)
class SalesOrder(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),          # Created after quotation approval
        ('in_progress', 'In Progress'),  # Production started
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    # ONE quotation = ONE order
    quotation = models.OneToOneField(
        'Quotation',
        on_delete=models.PROTECT,
        related_name='sales_order'
    )

    customer = models.ForeignKey(
        'Customer',
        on_delete=models.PROTECT,
        related_name='orders'
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_sales_orders'
    )

    # ADMIN acts as MANAGER (temporary)
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_sales_orders'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    order_date = models.DateTimeField(auto_now_add=True)
    expected_delivery_date = models.DateField(null=True, blank=True)
    remarks = models.TextField(blank=True)

    # VALIDATIONS
    def clean(self):
        # Guard (admin / migrations)
        if not self.quotation:
            return

        # Quotation must be approved
        if self.quotation.status != 'approved':
            raise ValidationError(
                "Sales order can only be created from an approved quotation."
            )

        # Manager required before production
        if self.status in ['in_progress', 'completed'] and not self.assigned_to:
            raise ValidationError(
                "Sales order must be assigned before processing."
            )

    def save(self, *args, **kwargs):
        skip_validation = kwargs.pop('skip_validation', False)

        if not skip_validation:
            self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"SalesOrder #{self.pk}"

    # WORK ORDER CREATION
    def create_work_orders(self, warehouse=None, created_by=None, wo_prefix=None):
        """
        Create WorkOrders ONLY when:
        - Quotation is approved
        - Order is pending
        - Admin (manager) is assigned
        """

        if self.status == 'in_progress':
            raise RuntimeError("Work orders already created for this order.")

        if self.status != 'pending':
            raise RuntimeError("Work orders can only be created from pending orders.")

        if not self.assigned_to:
            raise RuntimeError("Assign an admin before creating work orders.")

        from django.apps import apps

        WorkOrder = apps.get_model('production', 'WorkOrder')
        ProdProduct = apps.get_model('production', 'Product')
        Warehouse = apps.get_model('inventory', 'Warehouse')

        product_quantities = {}

        # Aggregate quotation items
        for item in self.quotation.items.all():
            product_quantities.setdefault(
                item.product.pk,
                {'product': item.product, 'quantity': 0}
            )
            product_quantities[item.product.pk]['quantity'] += item.quantity

        if not product_quantities:
            raise RuntimeError("Quotation has no items to produce.")

        created_wos = []

        with transaction.atomic():
            for idx, entry in enumerate(product_quantities.values(), start=1):
                inv_product = entry['product']
                quantity = entry['quantity']

                prod_product, _ = ProdProduct.objects.get_or_create(
                    name=inv_product.name,
                    defaults={
                        'category': getattr(inv_product, 'category', '') or '',
                        'size': getattr(inv_product, 'size', '') or '',
                        'color': getattr(inv_product, 'color', '') or '',
                        'description': getattr(inv_product, 'description', '') or '',
                    }
                )

                wh = (
                    warehouse
                    or getattr(inv_product, 'default_warehouse', None)
                    or Warehouse.objects.first()
                )

                if not wh:
                    raise RuntimeError("No warehouse available.")

                prefix = wo_prefix or f"SO{self.pk}"
                wo_number = (
                    f"{prefix}-{prod_product.pk}-"
                    f"{int(timezone.now().timestamp())}-{idx}"
                )

                wo = WorkOrder.objects.create(
                    work_order_number=wo_number,
                    product=prod_product,
                    sales_order=self,
                    quantity_to_produce=quantity,
                    warehouse=wh,
                    created_by=created_by or self.assigned_to
                )

                created_wos.append(wo)

            # Move order to production
            self.status = 'in_progress'
            self.save(skip_validation=True)

        return created_wos
