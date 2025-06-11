from rest_framework.permissions import BasePermission

class IsAdminUserOnly(BasePermission):
    """
    Дозволяє доступ лише адміністраторам.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff
