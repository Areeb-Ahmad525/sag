from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from users.models import UserProfile
from users import constants
from django.contrib.auth.models import User
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


from django import forms
from .models import Quotation


# QUOTATION FORM
class QuotationForm(forms.ModelForm):
    class Meta:
        model = Quotation
        fields = [
            'customer',
            'status',
            'notes',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Allow only safe statuses from form
        self.fields['status'].choices = [
            ('draft', 'Draft'),
            ('sent', 'Sent'),
        ]

        # Lock customer after creation
        if self.instance.pk:
            self.fields['customer'].disabled = True



class QuotationItemForm(forms.ModelForm):
    class Meta:
        model = QuotationItem
        fields = [
            'product_name',
            'description',
            'quantity',
            'unit_price',
        ]
        widgets = {
            'product_name': forms.TextInput(attrs={
                'placeholder': 'Item name (e.g. Window, Door)',
                'class': 'form-control'
            }),
            'description': forms.TextInput(attrs={
                'placeholder': 'Optional description',
                'class': 'form-control'
            }),
            'quantity': forms.NumberInput(attrs={
                'min': 1,
                'class': 'form-control'
            }),
            'unit_price': forms.NumberInput(attrs={
                'min': 0.01,
                'step': '0.01',
                'class': 'form-control'
            }),
        }

    # VALIDATIONS
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is None or quantity <= 0:
            raise forms.ValidationError("Quantity must be greater than 0.")
        return quantity

    def clean_unit_price(self):
        price = self.cleaned_data.get('unit_price')
        if price is None or price <= 0:
            raise forms.ValidationError("Unit price must be greater than 0.")
        return price


# FORMSET
QuotationItemFormSet = inlineformset_factory(
    Quotation,
    QuotationItem,
    form=QuotationItemForm,
    extra=0,
    can_delete=True,
    min_num=1,
    validate_min=True
)


# SALES ORDER FORM
class SalesOrderForm(forms.ModelForm):
    """
    SalesOrder is created ONLY from an approved quotation.
    Customer is auto-derived from quotation.
    Assigned_to uses Admin role from UserProfile (temporary manager).
    """

    class Meta:
        model = SalesOrder
        fields = [
            'quotation',
            'assigned_to',
            'expected_delivery_date',
            'remarks',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # TEMPORARY MANAGER = ADMIN USERS
        admin_user_ids = (
            UserProfile.objects
            .filter(
                role=constants.ROLE_MANAGER,
                status='active'
            )
            .values_list('user_id', flat=True)
        )

        self.fields['assigned_to'].queryset = User.objects.filter(
            id__in=admin_user_ids,
            is_active=True
        )

        self.fields['assigned_to'].label = "Assign Admin (Manager)"
        self.fields['assigned_to'].required = False

        # Lock quotation on edit
        if self.instance.pk:
            self.fields['quotation'].disabled = True

    def clean(self):
        cleaned_data = super().clean()
        quotation = cleaned_data.get('quotation')

        if not quotation:
            raise ValidationError(
                "Quotation is required to create a Sales Order."
            )

        # FIX: USE STATUS (NOT is_approved)
        if quotation.status != 'approved':
            raise ValidationError(
                "Only approved quotations can be converted into Sales Orders."
            )

        # Auto-set customer from quotation
        self.instance.customer = quotation.customer

        return cleaned_data