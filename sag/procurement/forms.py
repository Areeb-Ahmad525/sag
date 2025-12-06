from django import forms
from .models import PurchaseRequest, PurchaseRequestItem, PurchaseOrder, PurchaseOrderItem, GoodsReceived, GoodsReceivedItem
from inventory.models import Warehouse

class PurchaseRequestForm(forms.ModelForm):
    class Meta:
        model = PurchaseRequest
        fields = ['title','description','required_by','status']

class PurchaseRequestItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseRequestItem
        fields = ['material','quantity','unit','notes']

# Purchase Order
class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['po_number','supplier','expected_date','status','notes']

class PurchaseOrderItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderItem
        fields = ['material','quantity','unit_price']

# GRN
class GoodsReceivedForm(forms.ModelForm):
    class Meta:
        model = GoodsReceived
        fields = ['grn_number','po','supplier','warehouse','notes']

    # make warehouse choices explicit if needed
    warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.all())

class GoodsReceivedItemForm(forms.ModelForm):
    class Meta:
        model = GoodsReceivedItem
        fields = ['po_item','material','quantity','batch_reference']
