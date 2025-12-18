from django.contrib import admin, messages
from .models import (
    Customer,
    Quotation,
    QuotationItem,
    SalesOrder,
)

# CUSTOMER ADMIN

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'contact_person',
        'phone',
        'email',
        'status',
        'source',
        'created_at',
    )
    search_fields = ('name', 'phone', 'email')
    list_filter = ('status', 'source')
    readonly_fields = ('created_at', 'updated_at')


# QUOTATION ADMIN

class QuotationItemInline(admin.TabularInline):
    model = QuotationItem
    extra = 0


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'customer',
        'status',
        'total_price',
        'quotation_date',
        'approval_date',
        'created_by',
    )
    list_filter = ('status', 'quotation_date')
    search_fields = ('customer__name',)
    readonly_fields = (
        'total_price',
        'quotation_date',
        'approval_date',
        'created_by',
    )
    inlines = [QuotationItemInline]


# SALES ORDER ADMIN

@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'customer',
        'quotation',
        'assigned_to',
        'status',
        'order_date',
        'expected_delivery_date',
        'created_by',
    )

    list_filter = ('status', 'order_date')
    search_fields = ('customer__name',)
    readonly_fields = ('order_date', 'created_by')

    actions = ['create_work_orders_action']

    def create_work_orders_action(self, request, queryset):
        """
        SAFETY-CHECKED Admin action:
        Creates production WorkOrders from quotation items.
        """

        created_count = 0

        for so in queryset:
            # ---- Safety checks ----
            if not so.quotation:
                messages.error(
                    request,
                    f"SalesOrder #{so.pk} has no quotation."
                )
                continue

            if not so.assigned_to:
                messages.error(
                    request,
                    f"SalesOrder #{so.pk} is not assigned to any manager."
                )
                continue

            if so.status != 'in_progress':
                messages.error(
                    request,
                    f"SalesOrder #{so.pk} must be 'In-Progress' before sending to production."
                )
                continue

            # ---- Create Work Orders ----
            try:
                wos = so.create_work_orders(
                    created_by=so.assigned_to
                )
                created_count += len(wos)

            except Exception as e:
                messages.error(
                    request,
                    f"Failed for SalesOrder #{so.pk}: {e}"
                )

        if created_count:
            messages.success(
                request,
                f"{created_count} work order(s) created successfully."
            )

    create_work_orders_action.short_description = (
        "Send selected orders to Production"
    )
