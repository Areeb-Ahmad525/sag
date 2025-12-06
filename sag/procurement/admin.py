from django.contrib import admin
from .models import (
    PurchaseRequest, PurchaseRequestItem,
    PurchaseOrder, PurchaseOrderItem,
    GoodsReceived, GoodsReceivedItem
)

class PRItemInline(admin.TabularInline):
    model = PurchaseRequestItem
    extra = 1

@admin.register(PurchaseRequest)
class PurchaseRequestAdmin(admin.ModelAdmin):
    list_display = ('id','title','created_by','status','created_at','required_by')
    inlines = [PRItemInline]
    list_filter = ('status','created_at')

class POItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('po_number','supplier','status','created_by','created_at','expected_date')
    inlines = [POItemInline]
    list_filter = ('status','created_at','supplier')

class GRNItemInline(admin.TabularInline):
    model = GoodsReceivedItem
    extra = 1

@admin.register(GoodsReceived)
class GoodsReceivedAdmin(admin.ModelAdmin):
    list_display = ('grn_number','po','supplier','warehouse','status','created_at')
    inlines = [GRNItemInline]
    list_filter = ('status','created_at','supplier')
