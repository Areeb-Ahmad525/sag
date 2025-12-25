# utils.py
from django.core.mail import send_mail
from django.conf import settings

def notify_task_assignment(task):
    """Sends email when a task is first created/assigned"""
    subject = f"New Task Assigned: {task.title}"
    
    # Customize this message to match your exact needs
    message = (
        f"A new task has been assigned to you.\n\n"
        f"Assigned By: {task.manager.get_full_name()}\n"
        f"Task Title: {task.title}\n"
        f"Description: {task.description}\n"
        f"Deadline: {task.deadline}\n\n"
        f"Please log in to the factory portal to start working."
    )
    
    recipient = [task.employee.email]
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient)

def notify_task_completion(task):
    """Sends email back to manager when task is finished"""
    subject = f"Task Completed: {task.title}"
    message = (
        f"The following task has been marked as COMPLETED:\n\n"
        f"Task: {task.title}\n"
        f"Finished By: {task.employee.get_full_name()}\n"
        f"Completion Date: {task.updated_at}\n"
    )
    
    recipient = [task.manager.email]
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient)