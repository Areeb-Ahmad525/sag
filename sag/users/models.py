from django.db import models
from django.contrib.auth.models import User

ROLE_CHOICES = (
    ("admin", "Admin"),
    ("hr", "HR"),
    ("manager", "Manager"),
    ("employee", "Employee"),
    ("sweeper", "Sweeper"),
)

STATUS_CHOICES = (
    ("active", "Active"),
    ("inactive", "Inactive"),
)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    father_name = models.CharField(max_length=150, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="admin")
    profile_picture = models.ImageField(upload_to="profiles/", blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="active")

    def __str__(self):
        return self.name
