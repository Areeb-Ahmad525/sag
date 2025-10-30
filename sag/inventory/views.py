from django.shortcuts import redirect
from django.http import HttpResponse
from django.db.models import Sum
from django.shortcuts import render

from .models import Supplier, Warehouse, RawMaterial, InventoryBatch, StockMovement
from .forms import (
    SupplierForm,
    WarehouseForm,
    RawMaterialForm,
    InventoryBatchForm,
    StockMovementForm
)

def inventory_index(request):
    """
    Main index page for the Inventory Management section.
    Provides basic navigation links to all list views.
    """
    return render(request,'inventory_index.html')


# --- List Views (Displaying all records) ---

def supplier_list(request):
    suppliers = Supplier.objects.all().order_by('name')
    content = f"<h1>Suppliers ({suppliers.count()})</h1>"
    content += "<ul>" + "".join([f"<li>{s.name} - {s.email}</li>" for s in suppliers]) + "</ul>"
    content += '<p><a href="create/">Add New Supplier</a> | <a href="../">Back to Dashboard</a></p>'
    return HttpResponse(content)

def warehouse_list(request):
    warehouses = Warehouse.objects.all().order_by('name')
    content = f"<h1>Warehouses ({warehouses.count()})</h1>"
    content += "<ul>" + "".join([f"<li>{w.name} ({w.location[:30]}...)</li>" for w in warehouses]) + "</ul>"
    content += '<p><a href="create/">Add New Warehouse</a> | <a href="../">Back to Dashboard</a></p>'
    return HttpResponse(content)

def material_list(request):
    materials = RawMaterial.objects.all().order_by('type_name')
    content = f"<h1>Raw Materials ({materials.count()})</h1>"
    content += "<ul>" + "".join([f"<li>{m.get_type_name_display()} - Stock: {m.current_stock} ({m.unit})</li>" for m in materials]) + "</ul>"
    content += '<p><a href="create/">Add New Material</a> | <a href="../">Back to Dashboard</a></p>'
    return HttpResponse(content)

def batch_list(request):
    batches = InventoryBatch.objects.all().select_related('material', 'warehouse').order_by('-received_date')
    content = f"<h1>Inventory Batches ({batches.count()})</h1>"
    content += "<ul>" + "".join([f"<li>Batch {b.pk}: {b.material.get_type_name_display()} @ {b.warehouse.name} ({b.qty_available} units)</li>" for b in batches]) + "</ul>"
    content += '<p><a href="create/">Record New Batch</a> | <a href="../">Back to Dashboard</a></p>'
    return HttpResponse(content)

def movement_list(request):
    movements = StockMovement.objects.all().select_related('batch__material', 'from_warehouse', 'to_warehouse').order_by('-created_at')
    content = f"<h1>Stock Movements ({movements.count()})</h1>"
    content += "<ul>" + "".join([f"<li>{m.created_at.strftime('%Y-%m-%d %H:%M')}: {m.get_movement_type_display()} {m.qty} ({m.batch.material.get_type_name_display()})</li>" for m in movements]) + "</ul>"
    content += '<p><a href="create/">Record New Movement</a> | <a href="../">Back to Dashboard</a></p>'
    return HttpResponse(content)


# --- Create Views (Handling form submission) ---

def add_supplier(request):
    form = SupplierForm(request.POST or None) 
    
    if form.is_valid():
        form.save()
        # This redirect only happens if the form saved successfully
        return redirect('add_supplier') 
    
    # If it's a GET request or the form is invalid, render the template
    # The form variable is passed to the template via the context dictionary
    context = {'form': form}
    return render(request, 'add_supplier.html', context)

def add_warehouse(request):
    form = WarehouseForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('add_warehouse')
    context={'form':form}
    return render(request,'add_warehouse.html',context)

def add_raw_material(request):
    form = RawMaterialForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('add_raw_material')
    context={'form':form}
    return render(request,'add_raw_material.html',context)

def add_inventory_batch(request):
    form = InventoryBatchForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('add_inventory_batch')
    context={'form':form}
    return render(request,'inventory_batch.html',context)

def stock_movement(request):
    form = StockMovementForm(request.POST or None)
    if form.is_valid():
        # NOTE: A real system would use a signal or transaction here to update 
        # InventoryBatch.qty_available and RawMaterial.current_stock
        form.save()
        return redirect('stock_movement')
    context={'form':form}
    return render(request,'stock_movement.html',context)
