# inventory/urls.py
from django.urls import path
from . import views

app_name = 'inventory'
urlpatterns = [
    path('', views.inventory_index, name='inventory_base'),

    # Suppliers
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/create/', views.add_supplier, name='add_supplier'),
    path('supplier/<int:pk>/edit/', views.edit_supplier, name='edit_supplier'),
    path('supplier/<int:pk>/delete/', views.delete_supplier, name='delete_supplier'),


    # Warehouses
    path('warehouses/', views.warehouse_list, name='warehouse_list'),
    path('warehouses/create/', views.add_warehouse, name='add_warehouse'),
    path('warehouses/<int:pk>/edit/', views.edit_warehouse, name='edit_warehouse'),
    path('warehouses/<int:pk>/delete/', views.delete_warehouse, name='delete_warehouse'),


    # Raw materials
    path('materials/', views.material_list, name='material_list'),
    path('materials/create/', views.add_raw_material, name='add_raw_material'),
    path('materials/<int:pk>/edit/', views.edit_raw_material, name='edit_raw'),
    path('materials/<int:pk>/delete/', views.delete_raw_material, name='delete_raw'),

    # Batches
    path('batches/', views.batch_list, name='batch_list'),
    path('batches/create/', views.add_inventory_batch, name='add_inventory_batch'),
    path('batches/<int:pk>/edit/', views.edit_inventory_batch, name='edit_batch'),
    path('batches/<int:pk>/delete/', views.delete_inventory_batch, name='delete_batch'),

    # Movements
    path('movements/', views.movement_list, name='movement_list'),
    path('movements/create/', views.stock_movement, name='stock_movement'),
]
