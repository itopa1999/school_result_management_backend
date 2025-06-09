from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.utils import timezone
from .models import Parent

class ParentAccessCodeAuthentication(BaseAuthentication):
    def authenticate(self, request):
        access_code = request.headers.get('X-Parent-Code')
        if not access_code:
            return None

        try:
            parent = Parent.objects.get(access_code=access_code, is_active =True)
        except Parent.DoesNotExist:
            raise AuthenticationFailed('Invalid parent access code.')

        if parent.access_code_expired:
            raise AuthenticationFailed('Access code has expired.')

        return (parent, None)


