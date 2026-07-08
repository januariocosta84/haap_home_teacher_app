"""
Custom authentication backend that allows moe_auditing users to authenticate
with their email address instead of the default whatsapp_number field.
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailAuditingBackend(ModelBackend):
    """
    Authenticate moe_auditing users by email + password.
    Falls through to the default backend for all other roles.
    """

    def authenticate(self, request, email=None, password=None, **kwargs):
        if not email or not password:
            return None
        try:
            user = User.objects.get(email__iexact=email.strip(), role='moe_auditing')
        except User.DoesNotExist:
            User().set_password(password)  # mitigate timing attacks
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
