from django import forms

from .models import (
    WorkOrder,
    ProductionTask,
    WorkOrderConsumption,
    ProductionOutput,
    ProductionWastage,
)


# WORK ORDER FORM

class WorkOrderForm(forms.ModelForm):
    class Meta:
        model = WorkOrder
        fields = [
            'work_order_number',
            'product',
            'quantity_to_produce',
            'sales_order',
            'warehouse',
            'notes',
        ]

    def clean_quantity_to_produce(self):
        qty = self.cleaned_data['quantity_to_produce']
        if qty <= 0:
            raise forms.ValidationError("Quantity must be greater than zero.")
        return qty


# PRODUCTION TASK FORM
# NOTE:
# - work_order is injected in the view (NOT user editable)
# - status is controlled by task.start() / task.complete()
# - timestamps are automatic

class ProductionTaskForm(forms.ModelForm):
    class Meta:
        model = ProductionTask
        fields = [
            'stage',
            'title',
            'description',
            'assigned_to',
            'machine',
        ]


# RAW MATERIAL CONSUMPTION FORM

class ConsumptionForm(forms.ModelForm):
    class Meta:
        model = WorkOrderConsumption
        fields = [
            'raw_material',
            'batch',
            'quantity_used',
        ]

    def clean_quantity_used(self):
        qty = self.cleaned_data['quantity_used']
        if qty <= 0:
            raise forms.ValidationError("Quantity used must be greater than zero.")
        return qty


# PRODUCTION OUTPUT FORM
# NOTE:
# - work_order & created_by set in view
# - FinishedProductBatch created automatically

class OutputForm(forms.ModelForm):
    class Meta:
        model = ProductionOutput
        fields = [
            'product',
            'quantity_produced',
            'warehouse',
        ]

    def clean_quantity_produced(self):
        qty = self.cleaned_data['quantity_produced']
        if qty <= 0:
            raise forms.ValidationError("Produced quantity must be greater than zero.")
        return qty


# PRODUCTION WASTAGE FORM

class WastageForm(forms.ModelForm):
    class Meta:
        model = ProductionWastage
        fields = [
            'raw_material',
            'quantity_wasted',
            'reason',
        ]

    def clean_quantity_wasted(self):
        qty = self.cleaned_data['quantity_wasted']
        if qty <= 0:
            raise forms.ValidationError("Wastage quantity must be greater than zero.")
        return qty
