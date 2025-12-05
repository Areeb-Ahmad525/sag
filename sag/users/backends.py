from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

class EmailOrUsernameModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(email=username)  # login by email
        except User.DoesNotExist:
            try:
                user = User.objects.get(username=username)  # login by username
            except User.DoesNotExist:
                return None

        if user.check_password(password):
            return user
        return None
