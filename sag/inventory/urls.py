# inventory/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.inventory_index, name='inventory_base'),

    # Suppliers
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/create/', views.add_supplier, name='add_supplier'),

    # Warehouses
    path('warehouses/', views.warehouse_list, name='warehouse_list'),
    path('warehouses/create/', views.add_warehouse, name='add_warehouse'),

    # Raw materials
    path('materials/', views.material_list, name='material_list'),
    path('materials/create/', views.add_raw_material, name='add_raw_material'),

    # Batches
    path('batches/', views.batch_list, name='batch_list'),
    path('batches/create/', views.add_inventory_batch, name='add_inventory_batch'),

    # Movements
    path('movements/', views.movement_list, name='movement_list'),
    path('movements/create/', views.stock_movement, name='stock_movement'),
]
