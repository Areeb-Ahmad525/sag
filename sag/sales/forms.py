from django import forms
from django.forms import inlineformset_factory

from .models import (
    Customer,
    Quotation,
    QuotationItem,
    SalesOrder,
    SalesOrderItem
)



# CUSTOMER FORM 

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'name',
            'contact_person',
            'phone',
            'email',
            'address',
            'source',
            'status',
        ]


# QUOTATION FORM

class QuotationForm(forms.ModelForm):
    class Meta:
        model = Quotation
        fields = [
            'customer',
            'status',
            'notes',
        ]



# QUOTATION ITEM FORM

class QuotationItemForm(forms.ModelForm):
    class Meta:
        model = QuotationItem
        fields = [
            'product',       
            'description',
            'quantity',
            'unit_price',
        ]


QuotationItemFormSet = inlineformset_factory(
    Quotation,
    QuotationItem,
    form=QuotationItemForm,
    extra=1,
    can_delete=True
)


# SALES ORDER FORM
class SalesOrderForm(forms.ModelForm):
    class Meta:
        model = SalesOrder
        fields = [
            'quotation',
            'customer',
            'status',
            'expected_delivery_date',
            'remarks',
        ]



# SALES ORDER ITEM FORM
class SalesOrderItemForm(forms.ModelForm):
    class Meta:
        model = SalesOrderItem
        fields = [
            'material',      
            'description',
            'quantity',
            'unit_price',
        ]


SalesOrderItemFormSet = inlineformset_factory(
    SalesOrder,
    SalesOrderItem,
    form=SalesOrderItemForm,
    extra=1,
    can_delete=True
)
