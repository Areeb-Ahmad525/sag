from django import forms
from .models import WorkOrder, WorkOrderConsumption, ProductionOutput, ProductionWastage, Product, BOM, BOMItem, FinishedProductBatch

class WorkOrderForm(forms.ModelForm):
    class Meta:
        model = WorkOrder
        fields = ['work_order_number', 'product', 'quantity_to_produce', 'sales_order', 'warehouse', 'start_date', 'end_date', 'notes', 'status']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

class ConsumptionForm(forms.ModelForm):
    class Meta:
        model = WorkOrderConsumption
        fields = ['raw_material', 'batch', 'quantity_used']

class OutputForm(forms.ModelForm):
    class Meta:
        model = ProductionOutput
        fields = ['quantity_produced', 'product', 'warehouse']

class WastageForm(forms.ModelForm):
    class Meta:
        model = ProductionWastage
        fields = ['raw_material', 'quantity_wasted', 'reason']
