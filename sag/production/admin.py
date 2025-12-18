from django.contrib import admin
from .models import (
    ProductionStage, Product, BOM, BOMItem,
    WorkOrder, WorkOrderConsumption, ProductionOutput,
    FinishedProductBatch, ProductionWastage, ProductionStageLog
)

@admin.register(ProductionStage)
class ProductionStageAdmin(admin.ModelAdmin):
    list_display = ('sequence_no','name','is_active')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name','sku','category','is_active')

class BOMItemInline(admin.TabularInline):
    model = BOMItem
    extra = 1

@admin.register(BOM)
class BOMAdmin(admin.ModelAdmin):
    inlines = [BOMItemInline]
    list_display = ('product','version_no','created_at')

@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ('work_order_number','product','quantity_to_produce','sales_order','status','created_at')
    search_fields = ('work_order_number','product__name','sales_order__id','sales_order__customer__name')

@admin.register(WorkOrderConsumption)
class WorkOrderConsumptionAdmin(admin.ModelAdmin):
    list_display = ('work_order','raw_material','quantity_used','timestamp')

admin.site.register(ProductionOutput)
admin.site.register(FinishedProductBatch)
admin.site.register(ProductionWastage)
admin.site.register(ProductionStageLog)
