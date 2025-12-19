from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from users.decorators import role_required
from production.models import ProductionTask

from users.decorators import role_required
from inventory.models import InventoryBatch, StockMovement
from django.db.models import F, Sum

from .models import (
    WorkOrder,
    ProductionTask,
    WorkOrderConsumption,
    ProductionOutput,
    FinishedProductBatch,
    ProductionWastage,
)

from .forms import (
    WorkOrderForm,
    ProductionTaskForm,
    ConsumptionForm,
    OutputForm,
    WastageForm,
)


# DASHBOARD

from django.db.models import Count

from django.db.models import Count
from django.utils import timezone

@login_required
@role_required(['production', 'admin', 'manager'])
def production_index(request):
    # Work order stats
    total_wos = WorkOrder.objects.count()
    running = WorkOrder.objects.filter(status='in_progress').count()
    completed = WorkOrder.objects.filter(status='completed').count()

    # Task stats
    total_tasks = ProductionTask.objects.count()
    tasks_pending = ProductionTask.objects.filter(status='pending').count()
    tasks_in_progress = ProductionTask.objects.filter(status='in_progress').count()
    tasks_completed = ProductionTask.objects.filter(status='completed').count()

    # Tasks per user
    tasks_by_user_qs = (
        ProductionTask.objects
        .values('assigned_to__username')
        .annotate(task_count=Count('id'))
        .order_by('-task_count')
    )

    # Prepare tasks by user with percentage
    tasks_by_user = []
    for user in tasks_by_user_qs:
        user_name = user['assigned_to__username'] or "Unassigned"
        count = user['task_count']
        percent = round((count / total_tasks * 100), 2) if total_tasks > 0 else 0
        tasks_by_user.append({'username': user_name, 'count': count, 'percent': percent})

    context = {
        'total_wos': total_wos,
        'running': running,
        'completed': completed,
        'total_tasks': total_tasks,
        'tasks_pending': tasks_pending,
        'tasks_in_progress': tasks_in_progress,
        'tasks_completed': tasks_completed,
        'tasks_by_user': tasks_by_user,
        'today': timezone.now().date(),
    }

    return render(request, 'production/production_index.html', context)





# WORK ORDER CRUD


@login_required
@role_required(['production', 'admin'])
def wo_list(request):
    wos = WorkOrder.objects.select_related('product', 'warehouse').order_by('-created_at')
    return render(request, 'production/wo_list.html', {'wos': wos})


@login_required
@role_required(['production', 'admin'])
def wo_create(request):
    if request.method == 'POST':
        form = WorkOrderForm(request.POST)
        if form.is_valid():
            wo = form.save(commit=False)
            wo.created_by = request.user
            wo.save()
            messages.success(request, "Work order created successfully.")
            return redirect('production:wo_detail', wo_id=wo.id)
    else:
        form = WorkOrderForm()

    return render(request, 'production/wo_form.html', {'form': form})


@login_required
@role_required(['production', 'admin'])
def wo_update(request, wo_id):
    wo = get_object_or_404(WorkOrder, pk=wo_id)

    if wo.status != 'planned':
        messages.error(request, "Only planned work orders can be edited.")
        return redirect('production:wo_detail', wo_id=wo.id)

    if request.method == 'POST':
        form = WorkOrderForm(request.POST, instance=wo)
        if form.is_valid():
            form.save()
            messages.success(request, "Work order updated.")
            return redirect('production:wo_detail', wo_id=wo.id)
    else:
        form = WorkOrderForm(instance=wo)

    return render(request, 'production/wo_form.html', {'form': form})


@login_required
@role_required(['admin'])
@require_POST
def wo_delete(request, wo_id):
    wo = get_object_or_404(WorkOrder, pk=wo_id)

    if wo.tasks.exists():
        messages.error(request, "Cannot delete a work order with tasks.")
        return redirect('production:wo_detail', wo_id=wo.id)

    wo.delete()
    messages.success(request, "Work order deleted.")
    return redirect('production:wo_list')



# WORK ORDER DETAIL

from django.db.models import Sum

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from users.decorators import role_required

from .models import WorkOrder
from .forms import ProductionTaskForm, ConsumptionForm, OutputForm, WastageForm

@login_required
@role_required(['production', 'admin', 'manager'])
def wo_detail(request, wo_id):
    wo = get_object_or_404(
        WorkOrder.objects.prefetch_related('tasks', 'consumptions', 'outputs', 'wastages'),
        pk=wo_id
    )

    tasks = wo.tasks.select_related('assigned_to', 'stage')

    # Calculate produced, remaining, and progress %
    produced_qty = wo.outputs.aggregate(total=Sum('quantity_produced'))['total'] or 0
    remaining_qty = max(wo.quantity_to_produce - produced_qty, 0)
    progress_percent = 0
    if wo.quantity_to_produce > 0:
        progress_percent = round((produced_qty / wo.quantity_to_produce) * 100, 2)

    # Prepare form sections for template
    form_sections = [
        {
            'name': 'Consumption',
            'form': ConsumptionForm(),
            'icon': 'fa-arrow-up',
            'btn_text': 'Record Consumption'
        },
        {
            'name': 'Output',
            'form': OutputForm(),
            'icon': 'fa-plus',
            'btn_text': 'Add Output'
        },
        {
            'name': 'Wastage',
            'form': WastageForm(),
            'icon': 'fa-trash',
            'btn_text': 'Add Wastage'
        }
    ]

    context = {
        'wo': wo,
        'tasks': tasks,
        'produced_qty': produced_qty,
        'remaining_qty': remaining_qty,
        'progress_percent': progress_percent,
        'form_sections': form_sections,
    }

    return render(request, 'production/wo_detail.html', context)

# WORK ORDER STATUS

@login_required
@role_required(['production', 'admin', 'manager'])
@require_POST
def wo_start(request, wo_id):
    wo = get_object_or_404(WorkOrder, pk=wo_id)

    if wo.status != 'planned':
        messages.error(request, "Work order already started.")
        return redirect('production:wo_detail', wo_id=wo.id)

    if not wo.tasks.exists():
        messages.error(request, "Cannot start work order without tasks.")
        return redirect('production:wo_detail', wo_id=wo.id)

    wo.status = 'in_progress'
    wo.start_date = timezone.now().date()
    wo.save(update_fields=['status', 'start_date'])

    messages.success(request, "Work order started.")
    return redirect('production:wo_detail', wo_id=wo.id)


@login_required
@role_required(['production', 'admin'])
@require_POST
def wo_complete(request, wo_id):
    wo = get_object_or_404(WorkOrder, pk=wo_id)

    wo.auto_complete_if_ready()

    if wo.status == 'completed':
        messages.success(request, "Work order completed.")
    else:
        messages.error(request, "All tasks must be completed first.")

    return redirect('production:wo_detail', wo_id=wo.id)



# TASKS

@login_required
@role_required(['manager', 'admin'])
def task_create(request, wo_id):
    wo = get_object_or_404(WorkOrder, pk=wo_id)

    if request.method == 'POST':
        form = ProductionTaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.work_order = wo
            task.created_by = request.user
            task.save()
            messages.success(request, "Task created.")
            return redirect('production:wo_detail', wo_id=wo.id)
    else:
        form = ProductionTaskForm()

    return render(request, 'production/task_form.html', {'form': form})


@login_required
@role_required(['manager', 'admin'])
@require_POST
def task_start(request, task_id):
    task = get_object_or_404(ProductionTask, pk=task_id)

    with transaction.atomic():
        task.start()

    messages.success(request, "Task started.")
    return redirect('production:wo_detail', wo_id=task.work_order.id)


@login_required
@role_required(['manager', 'admin'])
@require_POST
def task_complete(request, task_id):
    task = get_object_or_404(ProductionTask, pk=task_id)

    with transaction.atomic():
        task.complete()

    messages.success(request, "Task completed.")
    return redirect('production:wo_detail', wo_id=task.work_order.id)


@login_required
@role_required(['manager', 'admin'])
@require_POST
def task_delete(request, task_id):
    task = get_object_or_404(ProductionTask, pk=task_id)
    wo_id = task.work_order.id
    task.delete()
    messages.success(request, "Task deleted.")
    return redirect('production:wo_detail', wo_id=wo_id)



@login_required
@role_required(['manager', 'admin'])
def task_list(request):
    """
    Display a list of all tasks across work orders.
    """
    # Fetch all tasks and prefetch related WorkOrder and assigned user to reduce queries
    tasks = ProductionTask.objects.select_related('work_order', 'assigned_to', 'stage').order_by('-created_at')

    return render(request, 'production/task_list.html', {
        'tasks': tasks,
    })



# RAW MATERIAL CONSUMPTION

@login_required
@role_required(['production', 'admin'])
def consumption_create(request, wo_id):
    wo = get_object_or_404(WorkOrder, pk=wo_id)

    if request.method == 'POST':
        form = ConsumptionForm(request.POST)
        if form.is_valid():
            cons = form.save(commit=False)
            cons.work_order = wo
            cons.created_by = request.user

            with transaction.atomic():
                batch = InventoryBatch.objects.select_for_update().get(
                    pk=cons.batch.pk
                )

                if cons.quantity_used > batch.qty_available:
                    messages.error(request, "Insufficient stock.")
                    return redirect('production:wo_detail', wo_id=wo.id)

                cons.save()

                batch.qty_available = F('qty_available') - cons.quantity_used
                batch.save(update_fields=['qty_available'])

                StockMovement.objects.create(
                    batch=batch,
                    from_warehouse=batch.warehouse,
                    to_warehouse=None,
                    qty=cons.quantity_used,
                    movement_type='OUT',
                    created_by=request.user
                )

            messages.success(request, "Consumption recorded.")
            return redirect('production:wo_detail', wo_id=wo.id)
    else:
        form = ConsumptionForm()

    return render(request, 'production/consumption_form.html', {'form': form})


@login_required
@role_required(['production', 'admin'])
@require_POST
def consumption_delete(request, consumption_id):
    cons = get_object_or_404(WorkOrderConsumption, pk=consumption_id)

    with transaction.atomic():
        batch = InventoryBatch.objects.select_for_update().get(
            pk=cons.batch.pk
        )

        batch.qty_available = F('qty_available') + cons.quantity_used
        batch.save(update_fields=['qty_available'])

        StockMovement.objects.create(
            batch=batch,
            from_warehouse=None,
            to_warehouse=batch.warehouse,
            qty=cons.quantity_used,
            movement_type='IN',
            created_by=request.user
        )

        cons.delete()

    messages.success(request, "Consumption removed and stock restored.")
    return redirect('production:wo_detail', wo_id=cons.work_order.id)


# OUTPUT

@login_required
@role_required(['production', 'admin'])
def output_create(request, wo_id):
    wo = get_object_or_404(WorkOrder, pk=wo_id)

    if wo.status != 'in_progress':
        messages.error(request, "Work order must be in progress.")
        return redirect('production:wo_detail', wo_id=wo.id)

    produced_qty = wo.outputs.aggregate(
        total=Sum('quantity_produced')
    )['total'] or 0

    remaining_qty = wo.quantity_to_produce - produced_qty

    if request.method == 'POST':
        form = OutputForm(request.POST)
        if form.is_valid():
            out = form.save(commit=False)

            if out.quantity_produced > remaining_qty:
                messages.error(
                    request,
                    f"Only {remaining_qty} units remaining to produce."
                )
                return redirect('production:wo_detail', wo_id=wo.id)

            out.work_order = wo
            out.created_by = request.user

            with transaction.atomic():
                out.save()
                FinishedProductBatch.objects.create(
                    product=out.product,
                    warehouse=out.warehouse,
                    qty_available=out.quantity_produced,
                    produced_date=timezone.now().date(),
                    work_order=wo
                )

            messages.success(request, "Production output recorded.")
            return redirect('production:wo_detail', wo_id=wo.id)
    else:
        form = OutputForm()

    return render(request, 'production/output_form.html', {'form': form})


# WASTAGE

@login_required
@role_required(['production', 'admin'])
def wastage_create(request, wo_id):
    wo = get_object_or_404(WorkOrder, pk=wo_id)

    if request.method == 'POST':
        form = WastageForm(request.POST)
        if form.is_valid():
            wastage = form.save(commit=False)
            wastage.work_order = wo
            wastage.created_by = request.user
            wastage.save()
            messages.success(request, "Wastage recorded.")
            return redirect('production:wo_detail', wo_id=wo.id)
    else:
        form = WastageForm()

    return render(request, 'production/wastage_form.html', {'form': form})
