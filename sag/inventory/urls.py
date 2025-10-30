from django.urls import path
from . import views

urlpatterns = [
    # Main Index/Dashboard
    path('', views.inventory_index, name='inventory_index'),

    # Supplier URLs (e.g., /suppliers/, /suppliers/create/)
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/create/', views.supplier_create, name='supplier_create'),

    # Warehouse URLs (e.g., /warehouses/, /warehouses/create/)
    path('warehouses/', views.warehouse_list, name='warehouse_list'),
    path('warehouses/create/', views.warehouse_create, name='warehouse_create'),

    # Raw Material URLs (e.g., /materials/, /materials/create/)
    path('materials/', views.material_list, name='material_list'),
    path('materials/create/', views.material_create, name='material_create'),

    # Inventory Batch URLs (e.g., /batches/, /batches/create/)
    path('batches/', views.batch_list, name='batch_list'),
    path('batches/create/', views.batch_create, name='batch_create'),

    # Stock Movement URLs (e.g., /movements/, /movements/create/)
    path('movements/', views.movement_list, name='movement_list'),
    path('movements/create/', views.movement_create, name='movement_create'),
]
