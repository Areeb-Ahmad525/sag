# inventory/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction,models
from django.contrib import messages
from django.urls import reverse
from django.db.models import Sum, F, Count
from django.utils import timezone
from django.db.models.functions import TruncMonth

from users.decorators import role_required  # use your users app decorator
from users.constants import ROLE_ADMIN, ROLE_INVENTORY  # central constants
from django.views.decorators.http import require_POST

from .models import Supplier, Warehouse, RawMaterial, InventoryBatch, StockMovement
from procurement.models import Quotation, PurchaseOrder
from .forms import SupplierForm, WarehouseForm, RawMaterialForm, InventoryBatchForm, StockMovementForm

# Allow admin & inventory roles to access inventory pages
ALLOWED_ROLES = [ROLE_ADMIN, ROLE_INVENTORY]


@login_required
@role_required(ALLOWED_ROLES)
def inventory_index(request):
    today = timezone.now().date()

    # Raw Materials
    total_materials = RawMaterial.objects.count()
    low_stock = RawMaterial.objects.filter(current_stock__lte=F('reorder_level'))
    out_of_stock = RawMaterial.objects.filter(current_stock=0)
    total_stock_qty = RawMaterial.objects.aggregate(total_qty=Sum('current_stock'))['total_qty'] or 0
    total_stock_value = 0  # Your RawMaterial model doesn't have unit_price, leave 0 or calculate if you add price

    # Inventory Batches
    total_batches = InventoryBatch.objects.count()
    batches_today = InventoryBatch.objects.filter(received_date=today).count()

    # Warehouses & Suppliers
    total_warehouses = Warehouse.objects.count()
    total_suppliers = Supplier.objects.count()

    # Stock Movements
    movements_today = StockMovement.objects.filter(created_at__date=today).count()
    movements_month = StockMovement.objects.filter(
        created_at__month=today.month,
        created_at__year=today.year
    ).count()

    context = {
        'total_materials': total_materials,
        'total_batches': total_batches,
        'total_warehouses': total_warehouses,
        'total_suppliers': total_suppliers,
        'low_stock': low_stock,
        'out_of_stock': out_of_stock,
        'total_stock_qty': total_stock_qty,
        'total_stock_value': total_stock_value,
        'batches_today': batches_today,
        'movements_today': movements_today,
        'movements_month': movements_month,
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
        return redirect('supplier_list')
    return render(request, 'inventory/add_supplier.html', {
        'form': form,
        'is_edit' : False,})

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

@login_required
@role_required(ALLOWED_ROLES)
def edit_supplier(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    form = SupplierForm(request.POST or None, instance=supplier)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Supplier updated.")
        return redirect('inventory:supplier_list')

    return render(request, 'inventory/add_supplier.html', {
        'form': form,
        'is_edit': True,
        'object': supplier,
    })

@login_required
@role_required(ALLOWED_ROLES)
def edit_warehouse(request, pk):
    warehouse = get_object_or_404(Warehouse, pk=pk)
    form = WarehouseForm(request.POST or None, instance=warehouse)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Warehouse updated.")
        return redirect('warehouse_list')

    return render(request, 'inventory/add_warehouse.html', {
        'form': form,
        'is_edit': True,
        'object': warehouse,
    })

@login_required
@role_required(ALLOWED_ROLES)
@require_POST
@login_required
@role_required(ALLOWED_ROLES)
def delete_supplier(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)

    if request.method == 'POST':
        # FK checks
        has_quotations = Quotation.objects.filter(supplier=supplier).exists()
        has_purchase_orders = PurchaseOrder.objects.filter(supplier=supplier).exists()

        if has_quotations or has_purchase_orders:
            messages.error(
                request,
                "Cannot delete supplier. It is linked to existing quotations or purchase orders."
            )
            return redirect('inventory:supplier_list')

        supplier.delete()
        messages.success(request, "Supplier deleted successfully.")
        return redirect('supplier_list')

    return redirect('supplier_list')


@login_required
@role_required(ALLOWED_ROLES)
@require_POST
def delete_warehouse(request, pk):
    warehouse = get_object_or_404(Warehouse, pk=pk)

    if request.method == 'POST':
        # FK checks
        has_batches = InventoryBatch.objects.filter(warehouse=warehouse).exists()
        has_movements_from = StockMovement.objects.filter(from_warehouse=warehouse).exists()
        has_movements_to = StockMovement.objects.filter(to_warehouse=warehouse).exists()

        if has_batches or has_movements_from or has_movements_to:
            messages.error(
                request,
                "Cannot delete warehouse. It is linked to inventory batches or stock movements."
            )
            return redirect('inventory:warehouse_list')

        warehouse.delete()
        messages.success(request, "Warehouse deleted successfully.")
        return redirect('inventory:warehouse_list')

    return redirect('inventory:warehouse_list')


@login_required
@role_required(ALLOWED_ROLES)
def edit_raw_material(request, pk):
    material = get_object_or_404(RawMaterial, pk=pk)
    form = RawMaterialForm(request.POST or None, instance=material)

    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            mat = form.save()
            # Always recalc stock after changes
            mat.recalc_current_stock()
        
        messages.success(request, "Raw material updated successfully.")
        return redirect('inventory:material_list')

    return render(request, 'inventory/add_raw_material.html', {
        'form': form,
        'is_edit': True,
        'object': material,
    })


@login_required
@role_required(ALLOWED_ROLES)
def delete_raw_material(request, pk):
    material = get_object_or_404(RawMaterial, pk=pk)

    if request.method == 'POST':
        # FK checks
        has_batches = InventoryBatch.objects.filter(material=material).exists()
        has_movements = StockMovement.objects.filter(batch__material=material).exists()

        if has_batches or has_movements:
            msgs = []
            if has_batches:
                msgs.append("inventory batches")
            if has_movements:
                msgs.append("stock movements")
            messages.error(
                request,
                f"Cannot delete raw material. It is linked to {', '.join(msgs)}."
            )
            return redirect('inventory:material_list')

        material.delete()
        messages.success(request, "Raw material deleted successfully.")
        return redirect('inventory:material_list')

    return redirect('inventory:material_list')


@login_required
@role_required(ALLOWED_ROLES)
def edit_inventory_batch(request, pk):
    batch = get_object_or_404(InventoryBatch, pk=pk)
    form = InventoryBatchForm(request.POST or None, instance=batch)

    if request.method == 'POST' and form.is_valid():
        try:
            with transaction.atomic():
                old_material = batch.material
                batch = form.save()
                
                # Recalculate stock for old and new material
                if batch.material != old_material:
                    old_material.recalc_current_stock()
                    batch.material.recalc_current_stock()
                else:
                    batch.material.recalc_current_stock()

            messages.success(request, "Inventory batch updated successfully.")
            return redirect('batch_list')
        except Exception as e:
            form.add_error(None, str(e))

    return render(request, 'inventory/inventory_batch.html', {
        'form': form,
        'is_edit': True,
        'object': batch,
    })


@login_required
@role_required(ALLOWED_ROLES)
def delete_inventory_batch(request, pk):
    batch = get_object_or_404(InventoryBatch, pk=pk)

    if request.method == 'POST':
        # Check for stock movements
        has_movements = StockMovement.objects.filter(batch=batch).exists()
        if has_movements:
            messages.error(
                request,
                "Cannot delete this batch. It is linked to stock movements."
            )
            return redirect('batch_list')

        try:
            with transaction.atomic():
                material = batch.material
                batch.delete()
                material.recalc_current_stock()

            messages.success(request, "Inventory batch deleted successfully.")
            return redirect('batch_list')
        except Exception as e:
            messages.error(request, f"Error deleting batch: {str(e)}")
            return redirect('batch_list')

    return redirect('batch_list')


