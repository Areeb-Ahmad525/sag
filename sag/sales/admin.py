from django.contrib import admin
from .models import (
    Customer,
    Quotation,
    QuotationItem,
    SalesOrder,
    SalesOrderItem
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

class SalesOrderItemInline(admin.TabularInline):
    model = SalesOrderItem
    extra = 0


@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'customer',
        'status',
        'order_date',
        'expected_delivery_date',
        'created_by',
    )
    list_filter = ('status', 'order_date')
    search_fields = ('customer__name',)
    readonly_fields = ('order_date', 'created_by')
    inlines = [SalesOrderItemInline]
