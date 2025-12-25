from django.db import models
from django.utils import timezone
from users.models import UserProfile

STATUS_CHOICES = (
    ('present', 'Present'),
    ('absent', 'Absent'),
)

class Attendance(models.Model):
    employee = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    remarks = models.TextField(blank=True)
    marked_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, related_name="marked_attendance")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('employee', 'date')  # One record per employee per day

    def is_editable(self):
        """
        Editable only within 6 hours of creation
        """
        return (timezone.now() - self.created_at).total_seconds() < 6 * 3600
