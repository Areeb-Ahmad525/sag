# users/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def role_required(allowed_roles=None):
    """
    Decorator to require the user's role to be one of allowed_roles.
    Pass strings exactly as stored in UserProfile.role (e.g., 'hr', 'admin', 'procurement').
    """
    if allowed_roles is None:
        allowed_roles = []

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "You must log in first.")
                return redirect("login")

            profile = getattr(request.user, "userprofile", None)

            if profile and profile.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                raise PermissionDenied("You do not have permission to view the procurement dashboard.")

            # messages.error(request, "You do not have permission to access this page.")
            return redirect("dashboard")
        return wrapper
    return decorator
