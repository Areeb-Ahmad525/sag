# users/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from . import constants

ROLE_CHOICES = (
    (constants.ROLE_ADMIN, "Admin"),
    (constants.ROLE_HR, "HR"),
    (constants.ROLE_PROCUREMENT, "Procurement"),
    (constants.ROLE_INVENTORY, "Inventory"),
    (constants.ROLE_SALES, "Sales"),
    (constants.ROLE_PRODUCTION, "Production"),
    (constants.ROLE_QC, "QC"),
    (constants.ROLE_MANAGER, "Manager"),
    (constants.ROLE_FINANCE, "Finance"),
    (constants.ROLE_EMPLOYEE, "Employee"),
    (constants.ROLE_SWEEPER, "Sweeper"),
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
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default=constants.ROLE_ADMIN)
    profile_picture = models.ImageField(upload_to="profiles/", blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="active")
    # Optionally add more fields later: address, hire_date, salary, etc.
    must_change_password = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.user.email})"

class LoginActivity(models.Model):
    STATUS_CHOICES = (
        ('success', 'Success'),
        ('failed', 'Failed'),
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    def __str__(self):
        uname = self.user.email if self.user else "Unknown"
        return f"{uname} - {self.status} at {self.login_time.isoformat()}"
    
class Team(models.Model):
    # Auto-incrementing primary key
    team_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    
    manager = models.ForeignKey(
        UserProfile, 
        on_delete=models.PROTECT, 
        related_name='managed_team',
        # Logic: Manager role check is handled in the Form for better flexibility
    )
    members = models.ManyToManyField(
        UserProfile, 
        related_name='member_of_teams',
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} (ID: {self.team_id})"