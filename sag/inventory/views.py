from django.shortcuts import redirect
from django.http import HttpResponse
from django.db.models import Sum

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
    content = """
        <h1 style="font-family: sans-serif;">Inventory Dashboard</h1>
        <p style="font-family: sans-serif;">Use the links below to manage your inventory data.</p>
        <ul style="font-family: sans-serif;">
            <li><a href="suppliers/">Manage Suppliers</a></li>
            <li><a href="warehouses/">Manage Warehouses</a></li>
            <li><a href="materials/">Manage Raw Materials</a></li>
            <li><a href="batches/">Manage Inventory Batches</a></li>
            <li><a href="movements/">Record Stock Movements</a></li>
        </ul>
    """
    return HttpResponse(content)


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

def supplier_create(request):
    form = SupplierForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('supplier_list')
    
    # Simple HTML rendering of the form
    html = f"""
        <h1 style="font-family: sans-serif;">Create New Supplier</h1>
        <form method="post" style="font-family: sans-serif;">
            <input type="hidden" name="csrfmiddlewaretoken" value="dummytoken">
            {form.as_p()}
            <button type="submit" style="padding: 10px; cursor: pointer;">Save Supplier</button>
        </form>
        <p><a href="../">Back to List</a></p>
    """
    return HttpResponse(html)

def warehouse_create(request):
    form = WarehouseForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('warehouse_list')
    html = f"""
        <h1 style="font-family: sans-serif;">Create New Warehouse</h1>
        <form method="post" style="font-family: sans-serif;">
            <input type="hidden" name="csrfmiddlewaretoken" value="dummytoken">
            {form.as_p()}
            <button type="submit" style="padding: 10px; cursor: pointer;">Save Warehouse</button>
        </form>
        <p><a href="../">Back to List</a></p>
    """
    return HttpResponse(html)

def material_create(request):
    form = RawMaterialForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('material_list')
    html = f"""
        <h1 style="font-family: sans-serif;">Create New Raw Material</h1>
        <form method="post" style="font-family: sans-serif;">
            <input type="hidden" name="csrfmiddlewaretoken" value="dummytoken">
            {form.as_p()}
            <button type="submit" style="padding: 10px; cursor: pointer;">Save Material</button>
        </form>
        <p><a href="../">Back to List</a></p>
    """
    return HttpResponse(html)

def batch_create(request):
    form = InventoryBatchForm(request.POST or None)
    if form.is_valid():
        # NOTE: A real system would use a signal or transaction here to update RawMaterial.current_stock
        form.save()
        return redirect('batch_list')
    html = f"""
        <h1 style="font-family: sans-serif;">Record New Inventory Batch</h1>
        <form method="post" style="font-family: sans-serif;">
            <input type="hidden" name="csrfmiddlewaretoken" value="dummytoken">
            {form.as_p()}
            <button type="submit" style="padding: 10px; cursor: pointer;">Save Batch</button>
        </form>
        <p><a href="../">Back to List</a></p>
    """
    return HttpResponse(html)

def movement_create(request):
    form = StockMovementForm(request.POST or None)
    if form.is_valid():
        # NOTE: A real system would use a signal or transaction here to update 
        # InventoryBatch.qty_available and RawMaterial.current_stock
        form.save()
        return redirect('movement_list')
    html = f"""
        <h1 style="font-family: sans-serif;">Record New Stock Movement</h1>
        <form method="post" style="font-family: sans-serif;">
            <input type="hidden" name="csrfmiddlewaretoken" value="dummytoken">
            {form.as_p()}
            <button type="submit" style="padding: 10px; cursor: pointer;">Save Movement</button>
        </form>
        <p><a href="../">Back to List</a></p>
    """
    return HttpResponse(html)
