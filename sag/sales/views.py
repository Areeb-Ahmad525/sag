from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.views.decorators.http import require_POST



from django.contrib.auth.decorators import login_required
from users.decorators import role_required

from utils.dbcrud import DBCRUD
from .models import Customer, Quotation, SalesOrder
from .forms import (
    CustomerForm,
    QuotationForm,
    QuotationItemFormSet,
    SalesOrderForm,
)
from production.models import ProductionOrder
from django.views.decorators.http import require_POST
from .utils import send_production_start_notification # Import the new function

@login_required
@require_POST
def send_to_production(request, pk):
    order = get_object_or_404(SalesOrder, pk=pk)

    # Only pending orders can go to production
    if order.status != 'pending':
        messages.error(request, 'This order cannot be sent to production.')
        return redirect('sales:order_list')

    # Update status
    order.status = 'in_progress'
    order.save()

    # --- EMAIL NOTIFICATION START ---
    if order.assigned_to and order.assigned_to.email:
        try:
            send_production_start_notification(order)
            messages.success(request, f'Order #{order.pk} is now In Progress. Notification sent to {order.assigned_to.get_full_name()}.')
        except Exception as e:
            messages.warning(request, 'Order moved to production, but notification email failed.')
    else:
        messages.success(request, 'Order sent to production successfully.')
    # --- EMAIL NOTIFICATION END ---

    return redirect('sales:order_list')
# CUSTOMER CRUD

def customer_list(request):
    return render(request, 'sales/customer_list.html', {
        'customers': Customer.objects.all()
    })

def customer_create(request):
    crud = DBCRUD(Customer, CustomerForm)
    result = crud.handle_create(request)

    if result['success']:
        messages.success(request, 'Customer created successfully')
        return redirect('sales:customer_list')

    messages.error(request, result.get('errors'))
    return render(request, 'sales/customer_form.html', {
        'form': result['form']
    })

def customer_update(request, pk):
    crud = DBCRUD(Customer, CustomerForm)
    result = crud.handle_update(request, pk)

    if result['success']:
        messages.success(request, 'Customer updated successfully')
        return redirect('sales:customer_list')

    messages.error(request, result.get('errors'))
    return render(request, 'sales/customer_form.html', {
        'form': result['form']
    })

@require_POST
def customer_delete(request, pk):
    crud = DBCRUD(Customer)
    result = crud.handle_delete(request, pk)

    if result['success']:
        messages.success(request, 'Customer deleted successfully')
    else:
        messages.error(request, result.get('errors', 'Delete failed'))

    return redirect('sales:customer_list')


# QUOTATION CRUD (WITH ITEMS)

def quotation_list(request):
    return render(request, 'sales/quotation_list.html', {
        'quotations': Quotation.objects.all()
    })

@transaction.atomic
def quotation_create(request):
    crud = DBCRUD(
        model=Quotation,
        form_class=QuotationForm,
        formset_class=QuotationItemFormSet,
        set_created_by=True,
    )

    result = crud.handle_create_with_formset(request)

    if result['success']:
        messages.success(request, 'Quotation created successfully')
        return redirect('sales:quotation_list')

    messages.error(request, result.get('errors'))
    return render(request, 'sales/quotation_form.html', {
        'form': result['form'],
        'formset': result['formset'],
    })

@transaction.atomic
def quotation_update(request, pk):
    quotation = get_object_or_404(Quotation, pk=pk)

    if quotation.status == 'approved':
        messages.error(request, 'Approved quotations cannot be edited.')
        return redirect('sales:quotation_list')

    crud = DBCRUD(
        model=Quotation,
        form_class=QuotationForm,
        formset_class=QuotationItemFormSet,
    )

    result = crud.handle_update_with_formset(request, pk)

    if result['success']:
        messages.success(request, 'Quotation updated successfully')
        return redirect('sales:quotation_list')
    
    if not result['success']:
        print(result['form'].errors)
        print(result['formset'].errors)
        print(result['formset'].non_form_errors())

    messages.error(request, result.get('errors', 'Please fix the errors below.'))
    return render(request, 'sales/quotation_form.html', {
        'form': result['form'],
        'formset': result['formset'],
    })


@require_POST
def quotation_delete(request, pk):
    quotation = get_object_or_404(Quotation, pk=pk)

    # Business rule stays intact
    if quotation.status != 'draft':
        messages.error(request, 'Only draft quotations can be deleted.')
        return redirect('sales:quotation_list')

    crud = DBCRUD(Quotation)
    result = crud.handle_delete(request, pk)

    if result.get('success'):
        messages.success(request, 'Quotation deleted successfully')
    else:
        messages.error(request, result.get('errors', 'Unable to delete quotation.'))

    return redirect('sales:quotation_list')

@transaction.atomic
def quotation_approve(request, pk):
    quotation = get_object_or_404(Quotation, pk=pk)

    if quotation.status == 'approved':
        messages.info(request, 'Quotation is already approved.')
        return redirect('sales:quotation_list')
    
    try:
        quotation.approve()

        customer = quotation.customer
        if customer.status != 'converted':
            customer.status = 'converted'
            customer.save(update_fields=['status'])

        messages.success(request, 'Quotation approved successfully')

    except ValueError as e:
        messages.error(request, str(e))

    return redirect('sales:quotation_list')


# SALES ORDERS (NO ITEMS)

def order_list(request):
    orders = (
        SalesOrder.objects
        .exclude(status='cancelled')
        .select_related('customer', 'assigned_to', 'quotation')
        .order_by('-order_date')
    )

    return render(request, 'sales/order_list.html', {
        'orders': orders
    })



def order_create(request):
    crud = DBCRUD(
        model=SalesOrder,
        form_class=SalesOrderForm,
        set_created_by=True,
    )

    result = crud.handle_create(request)

    if result['success']:
        order = result['object']

        # EXTRA SAFETY: block duplicate orders
        if SalesOrder.objects.filter(quotation=order.quotation).exclude(pk=order.pk).exists():
            order.delete()
            messages.error(
                request,
                "A sales order already exists for this quotation."
            )
            return redirect('sales:order_list')

        messages.success(request, 'Sales order created successfully')
        return redirect('sales:order_list')

    messages.error(request, result.get('errors'))
    return render(request, 'sales/order_form.html', {
        'form': result['form']
    })


def order_update(request, pk):
    order = get_object_or_404(SalesOrder, pk=pk)

    if order.status in ['in_progress', 'completed']:
        messages.error(
            request,
            "This order cannot be edited once production has started."
        )
        return redirect('sales:order_list')

    crud = DBCRUD(
        model=SalesOrder,
        form_class=SalesOrderForm,
    )

    result = crud.handle_update(request, pk)

    if result['success']:
        messages.success(request, 'Sales order updated successfully')
        return redirect('sales:order_list')

    messages.error(request, result.get('errors'))
    return render(request, 'sales/order_form.html', {
        'form': result['form']
    })


# # views.py
# from .utils import send_order_assignment_notification
# def order_create(request):
#     # 1. Initialize the CRUD utility
#     crud = DBCRUD(
#         model=SalesOrder,
#         form_class=SalesOrderForm,
#         set_created_by=True,
#     )

#     # 2. Process the request (Handles both GET and POST)
#     result = crud.handle_create(request)

#     # 3. Handle successful creation
#     if result['success']:
#         order = result['object']

#         # EXTRA SAFETY: Block duplicate orders
#         # Ensures no two SalesOrders can point to the same Quotation
#         if SalesOrder.objects.filter(quotation=order.quotation).exclude(pk=order.pk).exists():
#             order.delete()
#             messages.error(
#                 request,
#                 "A sales order already exists for this quotation."
#             )
#             return redirect('sales:order_list')

#         # EMAIL TRIGGER
#         # We send the mail after the safety check is passed
#         if order.assigned_to and order.assigned_to.email:
#             try:
#                 send_order_assignment_notification(order)
#                 messages.success(request, f'Sales order created and notification sent to {order.assigned_to.get_full_name()}.')
#             except Exception as e:
#                 # If email fails, we don't want to stop the user. 
#                 # We just warn them that the email didn't go out.
#                 messages.warning(request, 'Order created successfully, but notification email failed to send.')
#         else:
#             messages.success(request, 'Sales order created successfully (No manager assigned for email).')

#         return redirect('sales:order_list')

#     # 4. Handle Errors (Validation errors or GET request)
#     # If handle_create returns False, result['errors'] contains the form errors
#     error_msg = result.get('errors')
#     if error_msg:
#         messages.error(request, error_msg)

#     return render(request, 'sales/order_form.html', {
#         'form': result['form']
#     })


def order_delete(request, pk):
    order = get_object_or_404(SalesOrder, pk=pk)

    if order.status in ['in_progress', 'completed']:
        messages.error(
            request,
            "Orders in production or completed cannot be deleted."
        )
        return redirect('sales:order_list')

    crud = DBCRUD(SalesOrder)
    result = crud.handle_delete(request, pk)

    if result['success']:
        messages.success(request, 'Sales order deleted successfully')
        return redirect('sales:order_list')

    messages.error(request, result.get('errors'))
    return render(request, 'sales/order_confirm_delete.html', {
        'object': result['object']
    })


@login_required
@role_required(['admin','hr'])
def sales_base(request):
    return render(request, 'sales/base_sales.html')

