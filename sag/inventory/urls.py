from django.urls import path
from . import views

urlpatterns = [
    # Main Index
    path('', views.inventory_index, name='inventory_index'),

    # Supplier URLs 
    path('add_supplier/', views.add_supplier, name='add_supplier'),

    # Warehouse URLs 
    path('add_warehouse/', views.add_warehouse, name='add_warehouse'),

    # Raw Material URLs 
    path('add_raw_material/', views.add_raw_material, name='add_raw_material'),

    # Inventory Batch 
    path('add_inventory_batch/', views.add_inventory_batch, name='add_inventory_batch'),

    # Stock Movement URLs
    path('stock_movement/', views.stock_movement, name='stock_movement'),
]
