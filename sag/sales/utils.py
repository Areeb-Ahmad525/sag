# utils.py
from django.core.mail import send_mail
from django.conf import settings

def send_order_assignment_notification(order):
    """
    Sends an email to the User in 'assigned_to' when a SalesOrder 
    is assigned to them.
    """
    if not order.assigned_to or not order.assigned_to.email:
        return  # Skip if no user is assigned or user has no email

    subject = f"New Factory Order Assigned: {order}"
    
    # Extracting details from your model fields
    customer_name = order.customer.name if order.customer else "N/A"
    delivery_date = order.expected_delivery_date.strftime('%d %b %Y') if order.expected_delivery_date else "Not set"
    
    message = (
        f"Hello {order.assigned_to.get_full_name() or order.assigned_to.username},\n\n"
        f"You have been assigned as the manager for a new Sales Order.\n\n"
        f"--- ORDER DETAILS ---\n"
        f"Order ID: {order.pk}\n"
        f"Customer: {customer_name}\n"
        f"Quotation: {order.quotation}\n"
        f"Delivery Deadline: {delivery_date}\n"
        f"Remarks: {order.remarks}\n"
        f"----------------------\n\n"
        f"Please log in to the system to begin creating Work Orders."
    )

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [order.assigned_to.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"SMTP Error: {e}")



# utils.py
def send_production_start_notification(order):
    """
    Sends an email to the assigned manager when an order 
    is moved to 'in_progress' (Production).
    """
    # 1. ADD THIS CHECK: Ensure there is an email to send to
    if not order.assigned_to or not order.assigned_to.email:
        print(f"Skipping email: Order #{order.pk} has no assigned manager email.")
        return

    subject = f"PRODUCTION STARTED: Sales Order #{order.pk}"
    
    # 2. DATA CHECK: Ensure items exist to avoid errors
    items_summary = ""
    try:
        for item in order.quotation.items.all():
            items_summary += f"- {item.product.name} (Qty: {item.quantity})\n"
    except Exception as e:
        items_summary = "Item details currently unavailable."

    message = (
        f"Hello {order.assigned_to.first_name or order.assigned_to.username},\n\n"
        f"This is an automated notification that Sales Order #{order.pk} has been moved to PRODUCTION.\n\n"
        f"CUSTOMER: {order.customer.name if order.customer else 'N/A'}\n"
        f"EXPECTED DELIVERY: {order.expected_delivery_date or 'Not Specified'}\n\n"
        f"ITEMS TO PRODUCE:\n"
        f"{items_summary}\n"
        f"---------------------------------\n"
        f"Please ensure all materials are allocated and Work Orders are updated accordingly."
    )

    # 3. ADD TRY/EXCEPT: So we can see the exact error in the terminal
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [order.assigned_to.email],
            fail_silently=False,
        )
        print(f"Production email sent for Order #{order.pk}")
    except Exception as e:
        print(f"Production Email Error: {e}")