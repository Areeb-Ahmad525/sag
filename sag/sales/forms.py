from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError

from .models import (
    Customer,
    Quotation,
    QuotationItem,
    SalesOrder,
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
    """
    SalesOrder is created ONLY from an approved quotation.
    Customer is auto-derived from quotation.
    Assignment & production handover are NOT handled here.
    """

    class Meta:
        model = SalesOrder
        fields = [
            'quotation',
            'status',
            'expected_delivery_date',
            'remarks',
        ]

    def clean(self):
        cleaned_data = super().clean()
        quotation = cleaned_data.get('quotation')

        if not quotation:
            raise ValidationError("Quotation is required to create a Sales Order.")

        if quotation.status != 'approved':
            raise ValidationError(
                "Only approved quotations can be converted into Sales Orders."
            )

        self.instance.customer = quotation.customer

        return cleaned_data
