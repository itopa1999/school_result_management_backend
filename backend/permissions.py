# third party imports
from rest_framework import permissions
from rest_framework.permissions import BasePermission
from administrator.models import User


class IsClientPermission(BasePermission):

    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            return False

        if not user.is_superuser and not user.is_client:
            self.message = "You don't have access. Please contact support."
            return False

        return True


class IsDriverPermission(BasePermission):

    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            return False

        if not user.is_superuser and not user.is_driver:
            self.message = "You don't have access. Please contact support."
            return False

        return True