from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.decorators.http import require_POST

from users.decorators import role_required
from inventory.models import Product,InventoryBatch, StockMovement, RawMaterial, Warehouse
from .models import (
    WorkOrder, WorkOrderConsumption, ProductionOutput, FinishedProductBatch,
    ProductionWastage, ProductionStageLog, Product, BOM
)
from .forms import WorkOrderForm, ConsumptionForm, OutputForm, WastageForm

# Dashboard
@login_required
@role_required(['production','admin','manager'])
def production_index(request):
    # simple KPIs
    total_wos = WorkOrder.objects.count()
    running = WorkOrder.objects.filter(status='in_progress').count()
    completed = WorkOrder.objects.filter(status='completed').count()
    context = {
        'total_wos': total_wos,
        'running': running,
        'completed': completed,
    }
    return render(request, 'production/production_index.html', context)

# Work Orders
@login_required
@role_required(['production','admin'])
def wo_list(request):
    wos = WorkOrder.objects.all().order_by('-created_at')
    return render(request, 'production/wo_list.html', {'wos': wos})

@login_required
@role_required(['production','admin'])
def wo_create(request):
    if request.method == 'POST':
        form = WorkOrderForm(request.POST)
        if form.is_valid():
            wo = form.save(commit=False)
            wo.created_by = request.user
            wo.save()
            messages.success(request, "Work order created.")
            return redirect('production:wo_detail', wo_id=wo.id)
    else:
        form = WorkOrderForm()
    return render(request, 'production/wo_form.html', {'form': form})

@login_required
@role_required(['production','admin'])
def wo_detail(request, wo_id):
    wo = get_object_or_404(WorkOrder, pk=wo_id)
    consumption_form = ConsumptionForm()
    output_form = OutputForm(initial={'product': wo.product, 'warehouse': wo.warehouse})
    wastage_form = WastageForm()

    # add consumption
    if request.method == 'POST' and 'add_consumption' in request.POST:
        consumption_form = ConsumptionForm(request.POST)
        if consumption_form.is_valid():
            cons = consumption_form.save(commit=False)
            cons.work_order = wo
            cons.created_by = request.user
            # perform stock reduction as atomic operation
            try:
                with transaction.atomic():
                    # Ensure batch has enough qty
                    if cons.batch and float(cons.quantity_used) > float(cons.batch.qty_available):
                        messages.error(request, "Selected batch does not have enough quantity.")
                    else:
                        cons.save()
                        # create corresponding StockMovement (OUT)
                        StockMovement.objects.create(
                            batch = cons.batch,
                            from_warehouse = cons.batch.warehouse if cons.batch else None,
                            to_warehouse = None,
                            qty = int(cons.quantity_used) if cons.quantity_used == int(cons.quantity_used) else cons.quantity_used,
                            movement_type = 'OUT',
                            created_by = request.user
                        )
                        messages.success(request, "Consumption recorded and stock updated.")
                        return redirect('production:wo_detail', wo_id=wo.id)
            except Exception as e:
                messages.error(request, f"Error recording consumption: {e}")

    # add output
    if request.method == 'POST' and 'add_output' in request.POST:
        output_form = OutputForm(request.POST)
        if output_form.is_valid():
            out = output_form.save(commit=False)
            out.work_order = wo
            out.created_by = request.user
            with transaction.atomic():
                out.save()
                # create finished product batch
                fpb = FinishedProductBatch.objects.create(
                    product = out.product,
                    warehouse = out.warehouse,
                    qty_available = out.quantity_produced,
                    produced_date = out.timestamp.date() if hasattr(out, 'timestamp') else timezone.now().date(),
                    work_order = wo
                )
                messages.success(request, "Production output recorded and finished goods batch created.")
                # If WO completes automatically set status
                return redirect('production:wo_detail', wo_id=wo.id)

    # add wastage
    if request.method == 'POST' and 'add_wastage' in request.POST:
        wastage_form = WastageForm(request.POST)
        if wastage_form.is_valid():
            w = wastage_form.save(commit=False)
            w.work_order = wo
            w.created_by = request.user
            w.save()
            messages.success(request, "Wastage recorded.")
            return redirect('production:wo_detail', wo_id=wo.id)

    context = {
        'wo': wo,
        'consumption_form': consumption_form,
        'output_form': output_form,
        'wastage_form': wastage_form,
    }
    return render(request, 'production/wo_detail.html', context)

@login_required
@role_required(['production','admin'])
@require_POST
def wo_start(request, wo_id):
    wo = get_object_or_404(WorkOrder, pk=wo_id)

    if wo.status == 'planned':
        wo.status = 'in_progress'
        wo.start_date = timezone.now().date()  # ✔ now works
        wo.save()
        messages.success(request, "Work order started.")
    else:
        messages.warning(request, "Work order not in planned state.")

    return redirect('production:wo_detail', wo_id=wo.id)


@login_required
@role_required(['production','admin'])
@require_POST
def wo_complete(request, wo_id):
    wo = get_object_or_404(WorkOrder, pk=wo_id)

    if wo.status == 'in_progress':
        wo.status = 'completed'
        wo.end_date = timezone.now().date()   # ✔ now works
        wo.save()
        messages.success(request, "Work order marked as completed.")
    else:
        messages.warning(request, "Work order cannot be completed from current state.")

    return redirect('production:wo_detail', wo_id=wo.id)
