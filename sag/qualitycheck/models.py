from django.db import models
from django.contrib.auth.models import User


class QualityInspection(models.Model):
    INSPECTION_TYPE_CHOICES = [
        ('incoming', 'Incoming'),
        ('midline', 'Midline'),
        ('final', 'Final'),
    ]

    RESULT_CHOICES = [
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ]

    task_id = models.IntegerField(
        help_text="ID of the task being inspected (will be linked later)"
    )

    inspector = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='inspections'
    )

    inspection_type = models.CharField(
        max_length=20,
        choices=INSPECTION_TYPE_CHOICES
    )

    result = models.CharField(
        max_length=10,
        choices=RESULT_CHOICES
    )

    remarks = models.TextField(
        blank=True,
        null=True
    )

    inspection_date = models.DateField(auto_now_add=True)
    inspection_time = models.TimeField(auto_now_add=True)

    def __str__(self):
        return f"Task {self.task_id} - {self.inspection_type} - {self.result}"
