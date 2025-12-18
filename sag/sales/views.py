from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.utils import timezone

from utils.dbcrud import DBCRUD
from .models import Customer, Quotation, SalesOrder
from .forms import (
    CustomerForm,
    QuotationForm,
    QuotationItemFormSet,
    SalesOrderForm,
)

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


def customer_delete(request, pk):
    crud = DBCRUD(Customer)
    result = crud.handle_delete(request, pk)

    if result['success']:
        messages.success(request, 'Customer deleted successfully')
        return redirect('sales:customer_list')

    messages.error(request, result.get('errors'))
    return render(request, 'sales/customer_confirm_delete.html', {
        'object': result['object']
    })


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
        quotation = result['object']
        quotation.recalculate_total()
        messages.success(request, 'Quotation created successfully')
        return redirect('sales:quotation_list')

    messages.error(request, result.get('errors'))
    return render(request, 'sales/quotation_form.html', {
        'form': result['form'],
        'formset': result['formset'],
    })


@transaction.atomic
def quotation_update(request, pk):
    crud = DBCRUD(
        model=Quotation,
        form_class=QuotationForm,
        formset_class=QuotationItemFormSet,
    )

    result = crud.handle_update_with_formset(request, pk)

    if result['success']:
        quotation = result['object']
        quotation.recalculate_total()

        # approval handling
        if quotation.status == 'approved' and not quotation.approval_date:
            quotation.approval_date = timezone.now()
            quotation.save(update_fields=['approval_date'])

            customer = quotation.customer
            if customer.status != 'converted':
                customer.status = 'converted'
                customer.save(update_fields=['status'])

        messages.success(request, 'Quotation updated successfully')
        return redirect('sales:quotation_list')

    messages.error(request, result.get('errors'))
    return render(request, 'sales/quotation_form.html', {
        'form': result['form'],
        'formset': result['formset'],
    })


def quotation_delete(request, pk):
    crud = DBCRUD(Quotation)
    result = crud.handle_delete(request, pk)

    if result['success']:
        messages.success(request, 'Quotation deleted successfully')
        return redirect('sales:quotation_list')

    messages.error(request, result.get('errors'))
    return render(request, 'sales/quotation_confirm_delete.html', {
        'object': result['object']
    })


# SALES ORDERS (NO ITEMS)

def order_list(request):
    return render(request, 'sales/order_list.html', {
        'orders': SalesOrder.objects.select_related('customer', 'assigned_to')
    })


def order_create(request):
    crud = DBCRUD(
        model=SalesOrder,
        form_class=SalesOrderForm,
        set_created_by=True,
    )

    result = crud.handle_create(request)

    if result['success']:
        messages.success(request, 'Sales order created successfully')
        return redirect('sales:order_list')

    messages.error(request, result.get('errors'))
    return render(request, 'sales/order_form.html', {
        'form': result['form']
    })


def order_update(request, pk):
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


def order_delete(request, pk):
    crud = DBCRUD(SalesOrder)
    result = crud.handle_delete(request, pk)

    if result['success']:
        messages.success(request, 'Sales order deleted successfully')
        return redirect('sales:order_list')

    messages.error(request, result.get('errors'))
    return render(request, 'sales/order_confirm_delete.html', {
        'object': result['object']
    })
