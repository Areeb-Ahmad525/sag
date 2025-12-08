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
    return render(request, 'inventory/inventory_index.html', context)


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
        return redirect('supplier_list')
    return render(request, 'inventory/add_supplier.html', {'form': form})

@login_required
@role_required(ALLOWED_ROLES)
def add_warehouse(request):
    form = WarehouseForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Warehouse saved.")
        return redirect('warehouse_list')
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
        return redirect('material_list')
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
        return redirect('batch_list')
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
                    return redirect('movement_list')
            except Exception as e:
                # Catch validation errors raised during processing
                form.add_error(None, str(e))
    return render(request, 'inventory/stock_movement.html', {'form': form})
