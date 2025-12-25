from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.inventory_index, name='inventory_base'),

    # Suppliers
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/create/', views.add_supplier, name='add_supplier'),
    path('suppliers/edit/<int:pk>/', views.edit_supplier, name='edit_supplier'),
    path('suppliers/delete/<int:pk>/', views.delete_supplier, name='delete_supplier'),

    # Warehouses
    path('warehouses/', views.warehouse_list, name='warehouse_list'),
    path('warehouses/create/', views.add_warehouse, name='add_warehouse'),
    path('warehouses/edit/<int:pk>/', views.edit_warehouse, name='edit_warehouse'),
    path('warehouses/delete/<int:pk>/', views.delete_warehouse, name='delete_warehouse'),

    # Raw materials
    path('materials/', views.material_list, name='material_list'),
    path('materials/create/', views.add_raw_material, name='add_raw_material'),
    path('materials/edit/<int:pk>/', views.edit_raw_material, name='edit_raw_material'),
    path('materials/delete/<int:pk>/', views.delete_raw_material, name='delete_raw_material'),

    # Batches
    path('batches/', views.batch_list, name='batch_list'),
    path('batches/create/', views.add_inventory_batch, name='add_inventory_batch'),
    path('batches/edit/<int:pk>/', views.edit_inventory_batch, name='edit_inventory_batch'),
    path('batches/delete/<int:pk>/', views.delete_inventory_batch, name='delete_inventory_batch'),

    # Movements
    path('movements/', views.movement_list, name='movement_list'),
    path('movements/create/', views.stock_movement, name='stock_movement'),
    path('movements/edit/<int:pk>/', views.edit_stock_movement, name='edit_stock_movement'),
    path('movements/delete/<int:pk>/', views.delete_stock_movement, name='delete_stock_movement'),
]