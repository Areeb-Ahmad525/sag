from django.urls import path
from . import views

urlpatterns = [
    # Main Index/Dashboard
    # path('', views.inventory_index, name='inventory_index'),
    path('', views.inventory_index, name='inventory_index'),

    # Supplier URLs (e.g., /suppliers/, /suppliers/create/)
    # path('suppliers/', views.supplier_list, name='supplier_list'),
    path('add_supplier/', views.add_supplier, name='add_supplier'),

    # Warehouse URLs (e.g., /warehouses/, /warehouses/create/)
    # path('warehouses/', views.warehouse_list, name='warehouse_list'),
    path('add_warehouse/', views.add_warehouse, name='add_warehouse'),

    # Raw Material URLs (e.g., /materials/, /materials/create/)
    # path('materials/', views.material_list, name='material_list'),
    path('add_raw_material/', views.add_raw_material, name='add_raw_material'),

    # Inventory Batch URLs (e.g., /batches/, /batches/create/)
    path('batches/', views.batch_list, name='batch_list'),
    path('batches/create/', views.batch_create, name='batch_create'),

    # Stock Movement URLs (e.g., /movements/, /movements/create/)
    path('movements/', views.movement_list, name='movement_list'),
    path('movements/create/', views.movement_create, name='movement_create'),
]
