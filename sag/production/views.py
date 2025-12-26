from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils import timezone

from production.models import ProductionOrder, ProductionTask
from .forms import ProductionTaskForm
from users import constants


# =================================================
# PRODUCTION DASHBOARD
# =================================================
@login_required
def production_index(request):
    user = request.user
    profile = user.userprofile

    # Exclude completed orders
    base_qs = ProductionOrder.objects.exclude(status='completed')

    # -------------------------------
    # ROLE-BASED VISIBILITY
    # -------------------------------
    if profile.role == constants.ROLE_ADMIN:
        orders = base_qs

    elif profile.role == constants.ROLE_MANAGER:
        orders = base_qs.filter(manager=user)

    elif profile.role == constants.ROLE_EMPLOYEE:
        orders = base_qs.filter(
            tasks__assigned_to=user
        ).distinct()

    else:
        orders = ProductionOrder.objects.none()

    # -------------------------------
    # COUNTERS
    # -------------------------------
    total_orders = orders.count()

    status_counts = (
        orders.values('status')
        .annotate(count=Count('id'))
    )

    status_map = {row['status']: row['count'] for row in status_counts}

    context = {
        'orders': orders,
        'total_orders': total_orders,
        'draft': status_map.get('draft', 0),
        'waiting_inventory': status_map.get('waiting_inventory', 0),
        'ready': status_map.get('ready', 0),
        'in_progress': status_map.get('in_progress', 0),
        'waiting_qc': status_map.get('waiting_qc', 0),
    }

    return render(request, 'production/production_index.html', context)


# =================================================
# PRODUCTION ORDER DETAIL
# =================================================
@login_required
def production_order_detail(request, pk):
    order = get_object_or_404(ProductionOrder, pk=pk)

    user = request.user
    profile = user.userprofile

    # -------------------------------
    # ACCESS CONTROL
    # -------------------------------
    if profile.role == constants.ROLE_MANAGER and order.manager != user:
        messages.error(request, "You are not allowed to view this order.")
        return redirect('production:index')

    if profile.role == constants.ROLE_EMPLOYEE:
        if not order.tasks.filter(assigned_to=user).exists():
            messages.error(request, "You are not allowed to view this order.")
            return redirect('production:index')

    # -------------------------------
    # TASK VISIBILITY
    # -------------------------------
    if profile.role == constants.ROLE_EMPLOYEE:
        tasks = order.tasks.filter(assigned_to=user)
    else:
        tasks = order.tasks.all()

    # -------------------------------
    # QUOTATION ITEMS (READ-ONLY)
    # -------------------------------
    quotation_items = order.sales_order.quotation.items.all()

    context = {
        'order': order,
        'tasks': tasks,
        'quotation_items': quotation_items,
    }

    return render(request, 'production/production_order_detail.html', context)


# =================================================
# REQUEST INVENTORY (ADMIN + MANAGER)
# =================================================
@login_required
@require_POST
def request_inventory(request, pk):
    order = get_object_or_404(ProductionOrder, pk=pk)
    profile = request.user.userprofile

    # -------------------------------
    # ACCESS CONTROL
    # -------------------------------
    if profile.role not in (
        constants.ROLE_ADMIN,
        constants.ROLE_MANAGER,
    ):
        messages.error(request, "You are not allowed to request inventory.")
        return redirect('production:order_detail', pk=pk)

    if profile.role == constants.ROLE_MANAGER and order.manager != request.user:
        messages.error(request, "You are not allowed to request inventory for this order.")
        return redirect('production:order_detail', pk=pk)

    # -------------------------------
    # STATE VALIDATION
    # -------------------------------
    if order.status != 'draft':
        messages.warning(request, "Inventory request already sent.")
        return redirect('production:order_detail', pk=pk)

    # -------------------------------
    # STATE TRANSITION
    # draft → waiting_inventory
    # -------------------------------
    order.status = 'waiting_inventory'
    order.save()

    messages.success(request, "Inventory request sent successfully.")

    return redirect('production:order_detail', pk=pk)


# =================================================
# START PRODUCTION (ADMIN + MANAGER)
# =================================================
@login_required
@require_POST
def start_production(request, pk):
    order = get_object_or_404(ProductionOrder, pk=pk)
    profile = request.user.userprofile

    # -------------------------------
    # ACCESS CONTROL
    # -------------------------------
    if profile.role not in (
        constants.ROLE_ADMIN,
        constants.ROLE_MANAGER,
    ):
        messages.error(request, "You are not allowed to start production.")
        return redirect('production:order_detail', pk=pk)

    if profile.role == constants.ROLE_MANAGER and order.manager != request.user:
        messages.error(request, "You are not allowed to start this order.")
        return redirect('production:order_detail', pk=pk)

    # -------------------------------
    # STATE VALIDATION
    # -------------------------------
    if order.status != 'ready':
        messages.warning(
            request,
            f"Production cannot be started. Current status: {order.get_status_display()}"
        )
        return redirect('production:order_detail', pk=pk)

    # -------------------------------
    # STATE TRANSITION
    # ready → in_progress
    # -------------------------------
    order.status = 'in_progress'
    order.save()

    messages.success(request, "Production started successfully.")

    return redirect('production:order_detail', pk=pk)



@login_required
@require_POST
def complete_production(request, pk):
    order = get_object_or_404(ProductionOrder, pk=pk)
    profile = request.user.userprofile

    # Access control
    if profile.role not in (
        constants.ROLE_ADMIN,
        constants.ROLE_MANAGER,
    ):
        messages.error(request, "You are not allowed to complete production.")
        return redirect('production:order_detail', pk=pk)

    # State validation
    if order.status != 'in_progress':
        messages.warning(
            request,
            f'Cannot complete production. Current status: {order.get_status_display()}'
        )
        return redirect('production:order_detail', pk=pk)

    # State transition
    order.status = 'completed'
    order.completed_at = timezone.now()
    order.save()

    messages.success(request, "Production completed successfully.")

    # 🔥 Stay on same page
    return redirect('production:order_detail', pk=pk)




# @login_required
# def add_production_task(request, order_id):
#     order = get_object_or_404(ProductionOrder, id=order_id)
#     profile = request.user.userprofile

#     # Access control
#     if profile.role not in (constants.ROLE_ADMIN, constants.ROLE_MANAGER):
#         messages.error(request, "You are not allowed to add tasks.")
#         return redirect('production:order_detail', pk=order_id)

#     if profile.role == constants.ROLE_MANAGER and order.manager != request.user:
#         messages.error(request, "You cannot add tasks to this order.")
#         return redirect('production:order_detail', pk=order_id)

#     # 🔥 THIS IS THE FIX
#     order_manager_profile = order.manager.userprofile

#     if request.method == 'POST':
#         form = ProductionTaskForm(
#             request.POST,
#             manager_profile=order_manager_profile
#         )

#         if form.is_valid():
#             task = form.save(commit=False)
#             task.production_order = order
#             task.save()

#             messages.success(request, "Production task added successfully.")
#             return redirect('production:order_detail', pk=order_id)
#     else:
#         form = ProductionTaskForm(manager_profile=order_manager_profile)

#     return render(
#         request,
#         'production/add_task.html',
#         {
#             'order': order,
#             'form': form,
#         }
#     )

# views.py
from .utils import send_task_assignment_notification  # Import the function

def add_production_task(request, order_id):
    order = get_object_or_404(ProductionOrder, id=order_id)
    profile = request.user.userprofile

    # Access control
    if profile.role not in (constants.ROLE_ADMIN, constants.ROLE_MANAGER):
        messages.error(request, "You are not allowed to add tasks.")
        return redirect('production:order_detail', pk=order_id)

    if profile.role == constants.ROLE_MANAGER and order.manager != request.user:
        messages.error(request, "You cannot add tasks to this order.")
        return redirect('production:order_detail', pk=order_id)

    order_manager_profile = order.manager.userprofile

    if request.method == 'POST':
        form = ProductionTaskForm(
            request.POST,
            manager_profile=order_manager_profile
        )

        if form.is_valid():
            task = form.save(commit=False)
            task.production_order = order
            task.save()

            # 🔥 TRIGGER EMAIL NOTIFICATION
            try:
                send_task_assignment_notification(task)
                messages.success(request, f"Production task assigned and email sent to {task.assigned_to.username}.")
            except Exception:
                messages.warning(request, "Task saved, but notification email failed to send.")

            return redirect('production:order_detail', pk=order_id)
    else:
        form = ProductionTaskForm(manager_profile=order_manager_profile)

    return render(
        request,
        'production/add_task.html',
        {
            'order': order,
            'form': form,
        }
    )
    
    
    
@login_required
@require_POST
def start_task(request, task_id):
    task = get_object_or_404(ProductionTask, id=task_id)
    user = request.user

    # Only assigned employee can start
    if task.assigned_to != user:
        messages.error(request, "You are not allowed to start this task.")
        return redirect('production:order_detail', pk=task.production_order.id)

    if task.status != 'pending':
        messages.warning(request, "Task cannot be started.")
        return redirect('production:order_detail', pk=task.production_order.id)

    task.status = 'in_progress'
    task.started_at = timezone.now()
    task.save(update_fields=['status', 'started_at'])

    messages.success(request, "Task started successfully.")
    return redirect('production:order_detail', pk=task.production_order.id)



@login_required
@require_POST
def complete_task(request, task_id):
    task = get_object_or_404(ProductionTask, id=task_id)
    user = request.user

    # Only assigned employee can complete
    if task.assigned_to != user:
        messages.error(request, "You are not allowed to complete this task.")
        return redirect('production:order_detail', pk=task.production_order.id)

    if task.status != 'in_progress':
        messages.warning(request, "Task must be in progress to complete.")
        return redirect('production:order_detail', pk=task.production_order.id)

    task.status = 'completed'
    task.completed_at = timezone.now()
    task.save(update_fields=['status', 'completed_at'])

    messages.success(request, "Task completed successfully.")
    return redirect('production:order_detail', pk=task.production_order.id)




@login_required
def edit_task(request, task_id):
    task = get_object_or_404(ProductionTask, id=task_id)

    manager_profile = request.user.userprofile

    if request.method == 'POST':
        form = ProductionTaskForm(
            request.POST,
            instance=task,
            manager_profile=manager_profile
        )

        if form.is_valid():
            form.save()
            messages.success(request, "Task updated successfully.")
            return redirect(
                'production:order_detail',
                pk=task.production_order.id
            )
    else:
        form = ProductionTaskForm(
            instance=task,
            manager_profile=manager_profile
        )

    return render(
        request,
        'production/add_task.html',
        {
            'form': form,
            'task': task
        }
    )


