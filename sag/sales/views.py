from django.shortcuts import render, redirect
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
    SalesOrderItemFormSet,
)

# CUSTOMER CRUD 

def customer_list(request):
    crud = DBCRUD(Customer)
    return render(request, 'sales/customer_list.html', {
        'customers': crud.list()
    })


def customer_create(request):
    crud = DBCRUD(Customer, CustomerForm)
    result = crud.handle_create(request)

    if result['success']:
        messages.success(request, 'Customer created successfully')
        return redirect('sales:customer_list')

    if result['success'] is False:
        messages.error(request, result['errors'])

    return render(request, 'sales/customer_form.html', {
        'form': result['form']
    })


def customer_update(request, pk):
    crud = DBCRUD(Customer, CustomerForm)
    result = crud.handle_update(request, pk)

    if result['success']:
        messages.success(request, 'Customer updated successfully')
        return redirect('sales:customer_list')

    if result['success'] is False:
        messages.error(request, result['errors'])

    return render(request, 'sales/customer_form.html', {
        'form': result['form']
    })


def customer_delete(request, pk):
    crud = DBCRUD(Customer)
    result = crud.handle_delete(request, pk)

    if result['success']:
        messages.success(request, 'Customer deleted successfully')
        return redirect('sales:customer_list')

    if result['success'] is False:
        messages.error(request, result['errors'])

    return render(request, 'sales/customer_confirm_delete.html', {
        'object': result['object']
    })


# QUOTATION CRUD (PARENT + ITEMS)

def quotation_list(request):
    crud = DBCRUD(Quotation)
    return render(request, 'sales/quotation_list.html', {
        'quotations': crud.list()
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

        # Calculate quotation total
        quotation.calculate_total()

        messages.success(request, 'Quotation created successfully')
        return redirect('sales:quotation_list')

    if result['success'] is False:
        messages.error(request, result['errors'])

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

        # Recalculate total
        quotation.calculate_total()

        # On approval → set approval date + convert lead to customer
        if quotation.status == 'approved' and quotation.approval_date is None:
            quotation.approval_date = timezone.now()
            quotation.save(update_fields=['approval_date'])

            customer = quotation.customer
            if customer.status != 'converted':
                customer.status = 'converted'
                customer.save(update_fields=['status'])

        messages.success(request, 'Quotation updated successfully')
        return redirect('sales:quotation_list')

    if result['success'] is False:
        messages.error(request, result['errors'])

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

    if result['success'] is False:
        messages.error(request, result['errors'])

    return render(request, 'sales/quotation_confirm_delete.html', {
        'object': result['object']
    })


# SALES ORDER CRUD (PARENT + ITEMS)

def order_list(request):
    crud = DBCRUD(SalesOrder)
    return render(request, 'sales/order_list.html', {
        'orders': crud.list()
    })


@transaction.atomic
def order_create(request):
    crud = DBCRUD(
        model=SalesOrder,
        form_class=SalesOrderForm,
        formset_class=SalesOrderItemFormSet,
        set_created_by=True,
    )

    result = crud.handle_create_with_formset(request)

    if result['success']:
        order = result['object']

        # Ensure customer matches quotation (if selected)
        if order.quotation:
            order.customer = order.quotation.customer
            order.save(update_fields=['customer'])

        messages.success(request, 'Sales order created successfully')
        return redirect('sales:order_list')

    if result['success'] is False:
        messages.error(request, result['errors'])

    return render(request, 'sales/order_form.html', {
        'form': result['form'],
        'formset': result['formset'],
    })


@transaction.atomic
def order_update(request, pk):
    crud = DBCRUD(
        model=SalesOrder,
        form_class=SalesOrderForm,
        formset_class=SalesOrderItemFormSet,
    )

    result = crud.handle_update_with_formset(request, pk)

    if result['success']:
        messages.success(request, 'Sales order updated successfully')
        return redirect('sales:order_list')

    if result['success'] is False:
        messages.error(request, result['errors'])

    return render(request, 'sales/order_form.html', {
        'form': result['form'],
        'formset': result['formset'],
    })


def order_delete(request, pk):
    crud = DBCRUD(SalesOrder)
    result = crud.handle_delete(request, pk)

    if result['success']:
        messages.success(request, 'Sales order deleted successfully')
        return redirect('sales:order_list')

    if result['success'] is False:
        messages.error(request, result['errors'])

    return render(request, 'sales/order_confirm_delete.html', {
        'object': result['object']
    })
