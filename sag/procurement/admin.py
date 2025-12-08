# procurement/admin.py
from django.contrib import admin
from .models import (
    PurchaseRequest, PurchaseRequestItem,
    PurchaseOrder, PurchaseOrderItem,
    GoodsReceived, GoodsReceivedItem
)

class PurchaseRequestItemInline(admin.TabularInline):
    model = PurchaseRequestItem
    extra = 0

@admin.register(PurchaseRequest)
class PurchaseRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'created_by', 'status', 'created_at')
    inlines = [PurchaseRequestItemInline]
    ordering = ('-created_at',)


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 0

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'created_by', 'status', 'created_at')
    inlines = [PurchaseOrderItemInline]
    ordering = ('-created_at',)


class GoodsReceivedItemInline(admin.TabularInline):
    model = GoodsReceivedItem
    extra = 0

@admin.register(GoodsReceived)
class GoodsReceivedAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'warehouse', 'status', 'created_at')
    inlines = [GoodsReceivedItemInline]
    ordering = ('-created_at',)
