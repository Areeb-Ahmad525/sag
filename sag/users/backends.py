from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

class EmailOrUsernameModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Allow login via email. Since we save email into the username field,
        this ensures the user is found regardless of which field is checked.
        """
        if username is None:
            return None

        try:
            # Check email field specifically
            user = User.objects.get(email__iexact=username)
        except User.DoesNotExist:
            try:
                # Fallback to username field
                user = User.objects.get(username__iexact=username)
            except User.DoesNotExist:
                return None

        if user.check_password(password):
            return user
        return None