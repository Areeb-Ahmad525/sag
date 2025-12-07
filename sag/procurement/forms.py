# procurement/forms.py
from django import forms
from .models import (
    PurchaseRequest, PurchaseRequestItem,
    PurchaseOrder, PurchaseOrderItem,
    GoodsReceived, GoodsReceivedItem
)
from inventory.models import Supplier, RawMaterial, Warehouse

class PurchaseRequestForm(forms.ModelForm):
    class Meta:
        model = PurchaseRequest
        fields = ['title', 'description']


class PurchaseRequestItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseRequestItem
        fields = ['material', 'quantity', 'requested_date', 'notes']
        widgets = {
            'requested_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['supplier', 'expected_delivery', 'notes']
        widgets = {
            'expected_delivery': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }


class PurchaseOrderItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderItem
        fields = ['material', 'quantity', 'unit_price', 'notes']
        widgets = {
            'unit_price': forms.NumberInput(attrs={'step': '0.01'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }


class GoodsReceivedForm(forms.ModelForm):
    class Meta:
        model = GoodsReceived
        fields = ['po', 'supplier', 'warehouse', 'notes']  # supplier required
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }


class GoodsReceivedItemForm(forms.ModelForm):
    class Meta:
        model = GoodsReceivedItem
        fields = ['material', 'quantity', 'po_item', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def clean(self):
        cleaned = super().clean()
        material = cleaned.get('material')
        po_item = cleaned.get('po_item')
        if po_item and po_item.material != material:
            raise forms.ValidationError("Selected PO item material doesn't match the chosen material.")
        return cleaned
