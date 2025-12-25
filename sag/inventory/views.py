# inventory/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction,models
from django.contrib import messages
from django.urls import reverse

from users.decorators import role_required  # use your users app decorator
from users.constants import ROLE_ADMIN, ROLE_INVENTORY  # central constants

from .models import Supplier, Warehouse, RawMaterial, InventoryBatch, StockMovement
from .forms import SupplierForm, WarehouseForm, RawMaterialForm, InventoryBatchForm, StockMovementForm

# Allow admin & inventory roles to access inventory pages
ALLOWED_ROLES = [ROLE_ADMIN, ROLE_INVENTORY]

@login_required
@role_required(ALLOWED_ROLES)
def inventory_index(request):
    # Dashboard shows quick stats (counts) and low-stock items
    materials = RawMaterial.objects.all()
    batches = InventoryBatch.objects.all()
    low_stock = RawMaterial.objects.filter(current_stock__lte=models.F('reorder_level'))
    context = {
        'materials_count': materials.count(),
        'batches_count': batches.count(),
        'low_stock': low_stock,
    }
    return render(request, 'inventory/inventory_stats.html', context)


# LIST VIEWS
@login_required
@role_required(ALLOWED_ROLES)
def supplier_list(request):
    suppliers = Supplier.objects.all().order_by('name')
    return render(request, 'inventory/supplier_list.html', {'suppliers': suppliers})

@login_required
@role_required(ALLOWED_ROLES)
def warehouse_list(request):
    warehouses = Warehouse.objects.all().order_by('name')
    return render(request, 'inventory/warehouse_list.html', {'warehouses': warehouses})

@login_required
@role_required(ALLOWED_ROLES)
def material_list(request):
    materials = RawMaterial.objects.all().order_by('type_name')
    return render(request, 'inventory/material_list.html', {'materials': materials})

@login_required
@role_required(ALLOWED_ROLES)
def batch_list(request):
    batches = InventoryBatch.objects.select_related('material', 'warehouse').order_by('-received_date')
    return render(request, 'inventory/batch_list.html', {'batches': batches})

@login_required
@role_required(ALLOWED_ROLES)
def movement_list(request):
    movements = StockMovement.objects.all().select_related('batch__material', 'from_warehouse', 'to_warehouse', 'created_by').order_by('-created_at')
    return render(request, 'inventory/movement_list.html', {'movements': movements})


# CREATE / FORM VIEWS
@login_required
@role_required(ALLOWED_ROLES)
def add_supplier(request):
    form = SupplierForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Supplier saved.")
        return redirect('inventory:supplier_list')
    return render(request, 'inventory/add_supplier.html', {'form': form})

@login_required
@role_required(ALLOWED_ROLES)
def add_warehouse(request):
    form = WarehouseForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Warehouse saved.")
        return redirect('inventory:warehouse_list')
    return render(request, 'inventory/add_warehouse.html', {'form': form})

@login_required
@role_required(ALLOWED_ROLES)
def add_raw_material(request):
    form = RawMaterialForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        mat = form.save()
        # recalc stock just in case
        mat.recalc_current_stock()
        messages.success(request, "Raw material saved.")
        return redirect('inventory:material_list')
    return render(request, 'inventory/add_raw_material.html', {'form': form})

@login_required
@role_required(ALLOWED_ROLES)
def add_inventory_batch(request):
    form = InventoryBatchForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        batch = form.save()
        # After creating a batch, recalc parent material stock
        batch.material.recalc_current_stock()
        messages.success(request, "Inventory batch recorded.")
        return redirect('inventory:batch_list')
    return render(request, 'inventory/inventory_batch.html', {'form': form})

@login_required
@role_required(ALLOWED_ROLES)
def stock_movement(request):
    form = StockMovementForm(request.POST or None)
    if request.method == 'POST':
        form = StockMovementForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    movement = form.save(commit=False)
                    movement.created_by = request.user
                    movement.save()  # movement.save triggers processing (see model.save)
                    messages.success(request, "Stock movement recorded.")
                    return redirect('inventory:movement_list')
            except Exception as e:
                # Catch validation errors raised during processing
                form.add_error(None, str(e))
    return render(request, 'inventory/stock_movement.html', {'form': form})

@login_required
@role_required(ALLOWED_ROLES)
def edit_stock_movement(request, pk):
    movement = get_object_or_404(StockMovement, pk=pk)
    # Using the same form as the create view
    form = StockMovementForm(request.POST or None, instance=movement)
    
    if request.method == 'POST' and form.is_valid():
        try:
            with transaction.atomic():
                movement = form.save(commit=False)
                movement.updated_by = request.user # If you track updates
                movement.save()
                messages.success(request, "Stock movement updated.")
                return redirect('inventory:movement_list')
        except Exception as e:
            form.add_error(None, str(e))
            
    return render(request, 'inventory/stock_movement.html', {
        'form': form,
        'edit_mode': True,
        'movement': movement
    })

@login_required
@role_required(ALLOWED_ROLES)
def delete_stock_movement(request, pk):
    movement = get_object_or_404(StockMovement, pk=pk)
    # Delete immediately without a GET confirmation page
    movement.delete()
    messages.success(request, "Stock movement deleted.")
    return redirect('inventory:movement_list')


# --- SUPPLIER EDIT/DELETE ---
@login_required
@role_required(ALLOWED_ROLES)
def edit_supplier(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    form = SupplierForm(request.POST or None, instance=supplier)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Supplier updated.")
        return redirect('inventory:supplier_list')
    return render(request, 'inventory/add_supplier.html', {'form': form, 'edit_mode': True})

@login_required
@role_required(ALLOWED_ROLES)
def delete_supplier(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    supplier.delete()
    messages.success(request, "Supplier deleted.")
    return redirect('inventory:supplier_list')


# --- WAREHOUSE EDIT/DELETE ---
@login_required
@role_required(ALLOWED_ROLES)
def edit_warehouse(request, pk):
    warehouse = get_object_or_404(Warehouse, pk=pk)
    form = WarehouseForm(request.POST or None, instance=warehouse)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Warehouse updated.")
        return redirect('inventory:warehouse_list')
    return render(request, 'inventory/add_warehouse.html', {'form': form, 'edit_mode': True})

@login_required
@role_required(ALLOWED_ROLES)
def delete_warehouse(request, pk):
    warehouse = get_object_or_404(Warehouse, pk=pk)
    warehouse.delete()
    messages.success(request, "Warehouse deleted.")
    return redirect('inventory:warehouse_list')


# --- RAW MATERIAL EDIT/DELETE ---
@login_required
@role_required(ALLOWED_ROLES)
def edit_raw_material(request, pk):
    material = get_object_or_404(RawMaterial, pk=pk)
    form = RawMaterialForm(request.POST or None, instance=material)
    if request.method == 'POST' and form.is_valid():
        mat = form.save()
        mat.recalc_current_stock()
        messages.success(request, "Raw material updated.")
        return redirect('inventory:material_list')
    return render(request, 'inventory/add_raw_material.html', {'form': form, 'edit_mode': True})

@login_required
@role_required(ALLOWED_ROLES)
def delete_raw_material(request, pk):
    material = get_object_or_404(RawMaterial, pk=pk)
    material.delete()
    messages.success(request, "Raw material deleted.")
    return redirect('inventory:material_list')


# --- INVENTORY BATCH EDIT/DELETE ---
@login_required
@role_required(ALLOWED_ROLES)
def edit_inventory_batch(request, pk):
    batch = get_object_or_404(InventoryBatch, pk=pk)
    form = InventoryBatchForm(request.POST or None, instance=batch)
    if request.method == 'POST' and form.is_valid():
        batch = form.save()
        batch.material.recalc_current_stock()
        messages.success(request, "Inventory batch updated.")
        return redirect('inventory:batch_list')
    return render(request, 'inventory/inventory_batch.html', {'form': form, 'edit_mode': True})

@login_required
@role_required(ALLOWED_ROLES)
def delete_inventory_batch(request, pk):
    batch = get_object_or_404(InventoryBatch, pk=pk)
    material = batch.material
    batch.delete()
    material.recalc_current_stock() # Ensure stock is correct after deletion
    messages.success(request, "Inventory batch deleted.")
    return redirect('inventory:batch_list')
