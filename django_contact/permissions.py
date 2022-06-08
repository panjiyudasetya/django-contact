from rest_framework import permissions

from django_contact.models import ContactGroup


class IsGroupAdmin(permissions.BasePermission):

    def has_permission(self, request, view):
        return ContactGroup.objects.filter(
            group_id=view.kwargs['group_id'],
            contact__user=request.user,
            role=ContactGroup.ROLE_ADMIN
        ).exists()


class IsGroupMember(permissions.BasePermission):

    def has_permission(self, request, view):
        return ContactGroup.objects.filter(
            group_id=view.kwargs['group_id'],
            contact__user=request.user
        ).exists()
