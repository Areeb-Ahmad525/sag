# procurement/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.decorators import login_required

from users.decorators import role_required

from .models import (
    PurchaseRequest, PurchaseRequestItem,
    Quotation, QuotationItem,
    PurchaseOrder, PurchaseOrderItem,
    GoodsReceived, GoodsReceivedItem
)
from .forms import (
    PurchaseRequestForm, PurchaseRequestItemForm,
    QuotationForm, QuotationItemForm,
    PurchaseOrderForm, PurchaseOrderItemForm,
    GoodsReceivedForm, GoodsReceivedItemForm
)
from inventory.models import InventoryBatch, StockMovement, RawMaterial

# Procurement landing
@login_required
@role_required(['procurement','admin','hr'])
def procurement_index(request):
    # counts for dashboard
    pr_count = PurchaseRequest.objects.count()
    q_count = Quotation.objects.count()
    po_count = PurchaseOrder.objects.count()
    grn_count = GoodsReceived.objects.count()
    ctx = {
        'pr_count': pr_count,
        'q_count': q_count,
        'po_count': po_count,
        'grn_count': grn_count,
    }
    return render(request, 'procurement/procurement_index.html', ctx)


# --- PR views ---
@login_required
@role_required(['procurement','admin','manager'])
def pr_list(request):
    prs = PurchaseRequest.objects.order_by('-created_at')
    return render(request, 'procurement/pr_list.html', {'prs': prs})


@login_required
@role_required(['procurement','admin'])
def pr_create(request):
    if request.method == 'POST':
        form = PurchaseRequestForm(request.POST)
        if form.is_valid():
            pr = form.save(commit=False)
            pr.created_by = request.user
            pr.save()
            messages.success(request, "Purchase Request created.")
            return redirect('procurement:pr_detail', pr_id=pr.id)
    else:
        form = PurchaseRequestForm()
    return render(request, 'procurement/pr_form.html', {'form': form})


@login_required
@role_required(['procurement', 'admin'])
def pr_detail(request, pr_id):
    pr = get_object_or_404(PurchaseRequest, pk=pr_id)
    item_form = PurchaseRequestItemForm()

    can_approve = (
        pr.status == "submitted"
        and request.user.userprofile.role in ['admin', 'procurement']
    )

    if request.method == 'POST' and 'add_item' in request.POST:
        # Backend guard: only allow adding items when PR is in draft status
        if pr.status != 'draft':
            messages.error(request, "Items can only be added to PRs in draft status.")
            return redirect('procurement:pr_detail', pr_id=pr.id)

        item_form = PurchaseRequestItemForm(request.POST)
        if item_form.is_valid():
            item = item_form.save(commit=False)
            item.pr = pr
            item.save()
            messages.success(request, "Item added to PR.")
            return redirect('procurement:pr_detail', pr_id=pr.id)
        # if invalid, fall through to render with form errors

    return render(request, 'procurement/pr_detail.html', {
        'pr': pr,
        'item_form': item_form,
        'can_approve': can_approve,
    })



@login_required
@role_required(['procurement','admin'])
def pr_submit(request, pr_id):
    pr = get_object_or_404(PurchaseRequest, pk=pr_id)
    if pr.status != 'draft':
        messages.error(request, "Only draft PRs can be submitted.")
    else:
        pr.status = 'submitted'
        pr.save()
        messages.success(request, "PR submitted for approval.")
    return redirect('procurement:pr_detail', pr_id=pr.id)


@login_required
@role_required(['admin','procurement'])
def pr_approve(request, pr_id):
    pr = get_object_or_404(PurchaseRequest, pk=pr_id)
    if pr.status != 'submitted':
        messages.error(request, "Only submitted PRs can be approved.")
    else:
        pr.status = 'approved'
        pr.save()
        messages.success(request, "PR approved.")
    return redirect('procurement:pr_detail', pr_id=pr.id)


# --- Quotation views ---
@login_required
@role_required(['procurement','admin'])
def quotation_list(request):
    qs = Quotation.objects.order_by('-created_at')
    return render(request, 'procurement/quotation_list.html', {'quotations': qs})


@login_required
@role_required(['procurement','admin'])
def quotation_create(request):
    if request.method == 'POST':
        form = QuotationForm(request.POST)
        if form.is_valid():
            q = form.save(commit=False)
            q.created_by = request.user
            q.status = 'sent' if 'send' in request.POST else 'draft'
            q.save()
            messages.success(request, "Quotation saved.")
            return redirect('procurement:quotation_detail', q_id=q.id)
    else:
        form = QuotationForm()
    return render(request, 'procurement/quotation_form.html', {'form': form})


@login_required
@role_required(['procurement','admin'])
def quotation_detail(request, q_id):
    q = get_object_or_404(Quotation, pk=q_id)
    item_form = QuotationItemForm()
    
    # Handle adding an item
    if request.method == 'POST' and 'add_item' in request.POST:
        item_form = QuotationItemForm(request.POST)
        if item_form.is_valid():
            item = item_form.save(commit=False)
            item.quotation = q
            item.save()
            messages.success(request, "Item added to Quotation.")
            # Stay on the same page to show added item and errors if any
        else:
            messages.error(request, "Please correct the errors below.")

    # Prepare items with line totals
    items_with_total = []
    for it in q.items.all():
        line_total = (it.unit_price or 0) * it.quantity
        items_with_total.append((it, line_total))
    
    # Total amount for the quotation
    total_amount = sum(line_total for _, line_total in items_with_total)

    return render(request, 'procurement/quotation_detail.html', {
        'q': q,
        'item_form': item_form,
        'items_with_total': items_with_total,
        'total_amount': total_amount,
    })


@login_required
@role_required(['procurement','admin'])
def quotation_send(request, q_id):
    q = get_object_or_404(Quotation, pk=q_id)
    if q.status != 'draft':
        messages.info(request, "Quotation cannot be sent.")
        return redirect('procurement:quotation_detail', q_id=q.id)
    q.status = 'sent'
    q.save()
    messages.success(request, "Quotation sent successfully.")
    return redirect('procurement:quotation_detail', q_id=q.id)


@login_required
@role_required(['procurement','admin'])
def quotation_accept(request, q_id):
    """
    Accept a quotation — this typically triggers PO creation.
    We'll create a PO with items prefilled from quotation items and set quotation.status='accepted'.
    """
    q = get_object_or_404(Quotation, pk=q_id)
    if q.status == 'accepted':
        messages.info(request, "Quotation already accepted.")
        return redirect('procurement:quotation_detail', q_id=q.id)

    # create PO from this quotation
    po = PurchaseOrder.objects.create(
        supplier = q.supplier,
        created_by = request.user,
        status = 'draft',
    )
    # populate PO items
    for itm in q.items.all():
        PurchaseOrderItem.objects.create(
            po = po,
            material = itm.material,
            quantity = itm.quantity,
            unit_price = itm.unit_price or None
        )
    q.status = 'accepted'
    q.save()
    messages.success(request, f"Quotation accepted and PO#{po.pk} created.")
    return redirect('procurement:po_detail', po_id=po.id)


# --- PO views ---
@login_required
@role_required(['procurement','admin'])
def po_list(request):
    pos = PurchaseOrder.objects.order_by('-created_at')
    return render(request, 'procurement/po_list.html', {'pos': pos})


@login_required
@role_required(['procurement','admin'])
def po_create(request):
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST)
        if form.is_valid():
            po = form.save(commit=False)
            po.created_by = request.user
            po.save()
            messages.success(request, "Purchase Order created.")
            return redirect('procurement:po_detail', po_id=po.id)
    else:
        form = PurchaseOrderForm()
    return render(request, 'procurement/po_form.html', {'form': form})


@login_required
@role_required(['procurement','admin'])
def po_detail(request, po_id):
    po = get_object_or_404(PurchaseOrder, pk=po_id)
    item_form = PurchaseOrderItemForm()
    if request.method == 'POST' and 'add_item' in request.POST:
        item_form = PurchaseOrderItemForm(request.POST)
        if item_form.is_valid():
            item = item_form.save(commit=False)
            item.po = po
            item.save()
            messages.success(request, "Item added to PO.")
            return redirect('procurement:po_detail', po_id=po.id)
    return render(request, 'procurement/po_detail.html', {'po': po, 'item_form': item_form})


@login_required
@role_required(['procurement','admin'])
def po_send(request, po_id):
    po = get_object_or_404(PurchaseOrder, pk=po_id)
    if po.status == 'draft':
        po.status = 'sent'
        po.save()
        messages.success(request, "PO marked as sent to supplier.")
    else:
        messages.error(request, "Only draft PO can be sent.")
    return redirect('procurement:po_detail', po_id=po.id)


# --- GRN views ---
@login_required
@role_required(['procurement','admin','inventory'])
def grn_list(request):
    grns = GoodsReceived.objects.order_by('-created_at')
    return render(request, 'procurement/grn_list.html', {'grns': grns})


@login_required
@role_required(['procurement','admin'])
def grn_create(request):
    if request.method == 'POST':
        form = GoodsReceivedForm(request.POST)
        if form.is_valid():
            grn = form.save(commit=False)
            grn.created_by = request.user
            grn.save()
            messages.success(request, "GRN created.")
            return redirect('procurement:grn_detail', grn_id=grn.id)
    else:
        form = GoodsReceivedForm()
    return render(request, 'procurement/grn_form.html', {'form': form})


@login_required
@role_required(['procurement','admin'])
def grn_detail(request, grn_id):
    grn = get_object_or_404(GoodsReceived, pk=grn_id)
    item_form = GoodsReceivedItemForm()
    if request.method == 'POST' and 'add_item' in request.POST:
        item_form = GoodsReceivedItemForm(request.POST)
        if item_form.is_valid():
            item = item_form.save(commit=False)
            item.grn = grn
            item.save()
            messages.success(request, "Item added to GRN.")
            return redirect('procurement:grn_detail', grn_id=grn.id)
    return render(request, 'procurement/grn_detail.html', {'grn': grn, 'item_form': item_form})


@login_required
@role_required(['procurement','admin'])
@transaction.atomic
def grn_confirm(request, grn_id):
    """
    Confirm the GRN: update InventoryBatch and StockMovement and mark related PO items' received_quantity.
    This operation is atomic.
    """
    grn = get_object_or_404(GoodsReceived, pk=grn_id)
    if grn.status != 'received':
        messages.error(request, "Only received GRNs can be confirmed.")
        return redirect('procurement:grn_detail', grn_id=grn.id)

    for item in grn.items.all():
        # Create a new InventoryBatch for this GRN item or add to existing batch
        batch = InventoryBatch.objects.create(
            material = item.material,
            warehouse = grn.warehouse,
            qty_available = item.quantity,
            received_date = grn.created_at.date()
        )
        # Create StockMovement record (IN)
        StockMovement.objects.create(
            batch = batch,
            from_warehouse = None,
            to_warehouse = grn.warehouse,
            qty = item.quantity,
            movement_type = 'IN',
            created_by = request.user
        )

        # Update material current_stock quickly (recalc could be called elsewhere)
        item.material.recalc_current_stock()

        # If GRN references a PO item, update received quantity there
        if item.po_item:
            poi = item.po_item
            poi.received_quantity = (poi.received_quantity or 0) + item.quantity
            poi.save()

    grn.status = 'confirmed'
    grn.save()
    messages.success(request, "GRN confirmed and inventory updated.")
    return redirect('procurement:grn_detail', grn_id=grn.id)
