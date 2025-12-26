# utils.py
from django.core.mail import send_mail
from django.conf import settings

def send_task_assignment_notification(task):
    """
    Sends an email to the employee when a specific 
    Production Task is assigned to them.
    """
    if not task.assigned_to or not task.assigned_to.email:
        print(f"Skipping Task Email: No email found for user {task.assigned_to}")
        return

    subject = f"New Production Task: {task.name}"
    
    message = (
        f"Hello {task.assigned_to.get_full_name() or task.assigned_to.username},\n\n"
        f"A new production task has been assigned to you.\n\n"
        f"--- TASK DETAILS ---\n"
        f"Task Name: {task.name}\n"
        f"Production Order: PO #{task.production_order.id}\n"
        f"Status: {task.get_status_display()}\n"
        f"Remarks: {task.remarks or 'No remarks'}\n"
        f"--------------------\n\n"
        f"Please log in to your portal to start the task and update its progress.\n"
        f"Complete it before the production deadline."
    )

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [task.assigned_to.email],
            fail_silently=False,
        )
        print(f"Task email successfully sent to {task.assigned_to.email}")
    except Exception as e:
        print(f"Task Email Error: {e}")