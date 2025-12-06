# inventory/forms.py
from django import forms
from .models import Supplier, Warehouse, RawMaterial, InventoryBatch, StockMovement

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_person', 'phone_number', 'email']
        widgets = {'email': forms.EmailInput(attrs={'placeholder': 'supplier@example.com'})}

class WarehouseForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = ['name', 'location']
        widgets = {'location': forms.Textarea(attrs={'rows': 2})}

class RawMaterialForm(forms.ModelForm):
    class Meta:
        model = RawMaterial
        fields = ['type_name', 'category', 'unit', 'size', 'thickness', 'colour', 'reorder_level', 'supplier']

class InventoryBatchForm(forms.ModelForm):
    class Meta:
        model = InventoryBatch
        fields = ['material', 'warehouse', 'qty_available', 'received_date']
        widgets = {'received_date': forms.DateInput(attrs={'type': 'date'})}

    def clean_qty_available(self):
        qty = self.cleaned_data.get('qty_available')
        if qty is None:
            return 0
        if qty < 0:
            raise forms.ValidationError("Quantity available cannot be negative.")
        return qty

class StockMovementForm(forms.ModelForm):
    class Meta:
        model = StockMovement
        fields = ['batch', 'movement_type', 'qty', 'from_warehouse', 'to_warehouse']

        widgets = {
            'qty': forms.NumberInput(attrs={'min': 1}),
        }

    def clean(self):
        cleaned = super().clean()
        movement_type = cleaned.get('movement_type')
        from_wh = cleaned.get('from_warehouse')
        to_wh = cleaned.get('to_warehouse')
        batch = cleaned.get('batch')
        qty = cleaned.get('qty')

        # Basic validations
        if qty is None or qty <= 0:
            self.add_error('qty', "Quantity must be positive.")

        if not batch:
            raise forms.ValidationError("Batch is required.")

        if movement_type == 'IN':
            if from_wh:
                self.add_error('from_warehouse', "For 'Stock In', 'from warehouse' should be empty.")
        if movement_type == 'OUT':
            if to_wh:
                self.add_error('to_warehouse', "For 'Stock Out', 'to warehouse' should be empty.")
            # ensure enough stock
            if batch and qty and qty > batch.qty_available:
                self.add_error('qty', "Not enough quantity in selected batch.")
        if movement_type == 'TR':
            if not from_wh or not to_wh:
                raise forms.ValidationError("For 'Transfer', both 'from' and 'to' warehouses are required.")
            if from_wh == to_wh:
                self.add_error('to_warehouse', "From and To warehouse cannot be the same.")
            if batch and batch.warehouse != from_wh:
                self.add_error('batch', "Selected batch does not belong to the From warehouse.")
            if batch and qty and qty > batch.qty_available:
                self.add_error('qty', "Not enough quantity in selected batch for transfer.")
        if movement_type == 'ADJ':
            # adjustment allows positive or negative via qty sign — but form restricts min=1.
            # Here we treat qty as positive adjustment amount; if you need negative adjustments,
            # change UI/requirements. For now ADJ will be treated as +/- via an extra field.
            pass

        return cleaned
