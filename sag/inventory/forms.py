from django import forms
from .models import (
    Supplier,
    Warehouse,
    RawMaterial,
    InventoryBatch,
    StockMovement
)

# --- Form 1: Supplier ---
class SupplierForm(forms.ModelForm):
    """Form for creating and updating Supplier records."""
    class Meta:
        model = Supplier
        fields = [
            'name',
            'contact_person',
            'phone_number',
            'email'
        ]
        widgets = {
            'email': forms.EmailInput(attrs={'placeholder': 'supplier@example.com'}),
        }


# --- Form 2: Warehouse ---
class WarehouseForm(forms.ModelForm):
    """Form for creating and updating Warehouse locations."""
    class Meta:
        model = Warehouse
        fields = ['name', 'location']
        widgets = {
            'location': forms.Textarea(attrs={'rows': 2}),
        }


# --- Form 3: RawMaterial ---
class RawMaterialForm(forms.ModelForm):
    """Form for defining a new type of raw material."""
    class Meta:
        model = RawMaterial
        # Exclude 'current_stock' as this value should ideally be calculated/updated
        # via signals or business logic based on InventoryBatches and StockMovements.
        fields = [
            'type_name',
            'category',
            'unit',
            'size',
            'thickness',
            'colour',
            'reorder_level',
            'supplier'
        ]


# --- Form 4: InventoryBatch ---
class InventoryBatchForm(forms.ModelForm):
    """Form for recording the receipt of a new batch of material."""
    class Meta:
        model = InventoryBatch
        fields = [
            'material',
            'warehouse',
            'qty_available',
            'received_date'
        ]
        widgets = {
            # Use a DateInput widget for better user experience
            'received_date': forms.DateInput(attrs={'type': 'date'}),
        }

    # Custom clean method for validation (Example: ensure quantity is positive)
    def clean_qty_available(self):
        qty = self.cleaned_data.get('qty_available')
        if qty is not None and qty < 0:
            raise forms.ValidationError("Quantity available cannot be negative.")
        return qty


# --- Form 5: StockMovement ---
class StockMovementForm(forms.ModelForm):
    """Form for logging stock movements (IN, OUT, TR, ADJ)."""
    class Meta:
        model = StockMovement
        # Exclude 'created_at' as it is set automatically by auto_now_add=True
        fields = [
            'batch',
            'movement_type',
            'qty',
            'from_warehouse',
            'to_warehouse',
        ]
        widgets = {
            # Ensure the qty is never negative for input
            'qty': forms.NumberInput(attrs={'min': 1}),
        }

    # Custom validation to ensure 'from' and 'to' warehouses are logically set based on movement type
    def clean(self):
        cleaned_data = super().clean()
        movement_type = cleaned_data.get('movement_type')
        from_wh = cleaned_data.get('from_warehouse')
        to_wh = cleaned_data.get('to_warehouse')

        if movement_type == 'IN' and from_wh:
            self.add_error('from_warehouse', "For 'Stock In', the 'from warehouse' should be empty (stock is new).")
        
        if movement_type == 'OUT' and to_wh:
            self.add_error('to_warehouse', "For 'Stock Out', the 'to warehouse' should be empty (stock is consumed).")

        if movement_type == 'TR': # Transfer
            if not from_wh or not to_wh:
                raise forms.ValidationError("For a 'Transfer', both 'from warehouse' and 'to warehouse' must be specified.")
            if from_wh == to_wh:
                self.add_error('to_warehouse', "The 'from' and 'to' warehouses cannot be the same for a Transfer.")
            
        return cleaned_data
