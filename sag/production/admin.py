from django.contrib import admin

from .models import (
    ProductionStage,
    BOM,
    BOMItem,
    WorkOrder,
    WorkOrderConsumption,
    ProductionOutput,
    FinishedProductBatch,
    ProductionWastage,
    ProductionStageLog,
)

# PRODUCTION STAGES

@admin.register(ProductionStage)
class ProductionStageAdmin(admin.ModelAdmin):
    list_display = ('sequence_no', 'name', 'is_active')
    list_display_links = ('name',)      
    list_editable = ('sequence_no', 'is_active')
    ordering = ('sequence_no',)
    search_fields = ('name',)


# BILL OF MATERIALS (BOM)

class BOMItemInline(admin.TabularInline):
    model = BOMItem
    extra = 1
    autocomplete_fields = ('raw_material',)


@admin.register(BOM)
class BOMAdmin(admin.ModelAdmin):
    list_display = ('product', 'version_no', 'created_at')
    list_filter = ('product',)
    search_fields = ('product__name', 'version_no')
    autocomplete_fields = ('product',)
    inlines = [BOMItemInline]
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)


# WORK ORDERS

class WorkOrderConsumptionInline(admin.TabularInline):
    model = WorkOrderConsumption
    extra = 0
    readonly_fields = ('timestamp',)


class ProductionOutputInline(admin.TabularInline):
    model = ProductionOutput
    extra = 0
    readonly_fields = ('timestamp',)


class ProductionWastageInline(admin.TabularInline):
    model = ProductionWastage
    extra = 0
    readonly_fields = ('timestamp',)


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = (
        'work_order_number',
        'product',
        'quantity_to_produce',
        'sales_order',
        'status',
        'created_at',
    )

    list_filter = ('status', 'created_at', 'product')
    search_fields = (
        'work_order_number',
        'product__name',
        'sales_order__id',
        'sales_order__customer__name',
    )

    list_select_related = ('product', 'sales_order')
    date_hierarchy = 'created_at'
    autocomplete_fields = ('product', 'sales_order', 'warehouse')

    inlines = [
        WorkOrderConsumptionInline,
        ProductionOutputInline,
        ProductionWastageInline,
    ]

    fieldsets = (
        ('Basic Info', {
            'fields': (
                'work_order_number',
                'product',
                'quantity_to_produce',
                'warehouse',
                'sales_order',
            )
        }),
        ('Status & Dates', {
            'fields': (
                'status',
                'start_date',
                'end_date',
            )
        }),
        ('Meta', {
            'fields': (
                'created_by',
                'created_at',
                'notes',
            )
        }),
    )

    readonly_fields = ('created_at', 'created_by')


# RAW MATERIAL CONSUMPTION

@admin.register(WorkOrderConsumption)
class WorkOrderConsumptionAdmin(admin.ModelAdmin):
    list_display = ('work_order', 'raw_material', 'quantity_used', 'batch', 'timestamp')
    list_filter = ('raw_material', 'timestamp')
    search_fields = ('work_order__work_order_number', 'raw_material__name')
    list_select_related = ('work_order', 'raw_material', 'batch')
    autocomplete_fields = ('work_order', 'raw_material', 'batch')
    readonly_fields = ('timestamp',)


# PRODUCTION OUTPUT

@admin.register(ProductionOutput)
class ProductionOutputAdmin(admin.ModelAdmin):
    list_display = ('work_order', 'product', 'quantity_produced', 'warehouse', 'timestamp')
    list_filter = ('product', 'warehouse', 'timestamp')
    search_fields = ('work_order__work_order_number', 'product__name')
    autocomplete_fields = ('work_order', 'product', 'warehouse')
    readonly_fields = ('timestamp',)


@admin.register(FinishedProductBatch)
class FinishedProductBatchAdmin(admin.ModelAdmin):
    list_display = ('product', 'warehouse', 'qty_available', 'produced_date', 'work_order')
    list_filter = ('warehouse', 'produced_date')
    search_fields = ('product__name', 'work_order__work_order_number')
    autocomplete_fields = ('product', 'warehouse', 'work_order')


# WASTAGE

@admin.register(ProductionWastage)
class ProductionWastageAdmin(admin.ModelAdmin):
    list_display = ('work_order', 'raw_material', 'quantity_wasted', 'timestamp')
    list_filter = ('raw_material', 'timestamp')
    search_fields = ('work_order__work_order_number', 'raw_material__name')
    autocomplete_fields = ('work_order', 'raw_material')
    readonly_fields = ('timestamp',)


# STAGE LOGS (READ ONLY)

@admin.register(ProductionStageLog)
class ProductionStageLogAdmin(admin.ModelAdmin):
    list_display = ('work_order', 'stage', 'status', 'started_at', 'completed_at')
    list_filter = ('status', 'stage')
    search_fields = ('work_order__work_order_number', 'stage__name')
    readonly_fields = (
        'work_order',
        'stage',
        'status',
        'started_at',
        'completed_at',
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
