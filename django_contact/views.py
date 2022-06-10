from django.db.models import QuerySet
from django.http import Http404
from drf_rw_serializers import generics as rw_generics
from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.serializers import Serializer as EmptySerializer
from typing import Dict, List, Union

from django_contact.models import (
    Contact,
    Group
)
from django_contact.permissions import (
    IsGroupAdmin,
    IsGroupMember
)
from django_contact.serializers import (
    ContactSerializer,
    ContactDeserializer,
    PhoneSerializer,
    PhoneDeserializer,
    MyContactSerializer,
    MyContactCreateDeserializer,
    MyContactUpdateDeserializer,
    GroupSerializer,
    GroupDeserializer,
    ContactGroupSerializer,
    ContactGroupCreateDeserializer,
    ContactGroupUpdateDeserializer,
)


class BaseContactView(rw_generics.GenericAPIView):
    read_serializer_class = ContactSerializer
    write_serializer_class = ContactDeserializer

    def get_permissions(self) -> List[permissions.BasePermission]:
        if self.request.method == 'GET':
            self.permission_classes = [permissions.IsAuthenticated]
        else:
            self.permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        return super().get_permissions()

    def get_queryset(self):
        """
        Returns all `Contact` instances with prefetched phone numbers.
        """
        return Contact.objects.all().prefetch_phone_numbers().order_by('id')


class ContactListView(
    BaseContactView,
    rw_generics.ListAPIView,
    rw_generics.CreateAPIView
):
    """
    Interface:
    - `GET /contacts/`: Get all contacts.
    - `POST /contacts/`: Create a new contact.
    """
    pass


class ContactDetailView(
    BaseContactView,
    rw_generics.RetrieveAPIView,
    rw_generics.UpdateAPIView,
    generics.DestroyAPIView
):
    """
    Interface:
    - `GET /contacts/{pk}/`: Retrieve contact with specific ID.
    - `PUT /contacts/{pk}/`: Update contact with specific ID.
    - `DELETE /contacts/{pk}/`: Delete contact with specific ID.
    """
    pass


class BasePhoneView(rw_generics.GenericAPIView):
    read_serializer_class = PhoneSerializer
    write_serializer_class = PhoneDeserializer
    permission_classes = [permissions. IsAuthenticated, permissions.IsAdminUser]

    def get_contact(self) -> Contact:
        """
        Return `Contact` object belongs to the given contact ID.
        """
        try:
            return Contact.objects.get(user=self.kwargs['contact_id'])
        except Contact.DoesNotExist:
            raise Http404

    def get_queryset(self) -> QuerySet[Contact]:
        """
        Returns `Phone` instances belongs to the given contact ID
        with annotated `is_primary` data.
        """
        contact = self.get_contact()
        return contact.phone_numbers.all().order_by('id')

    def get_serializer_context(self) -> Dict:
        """
        We override this method because the write serializer class
        expecting `Contact` object of the given contact ID.
        """
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            context = super().get_serializer_context()
            context.update({'contact': self.get_contact()})
            return context

        return super().get_serializer_context()


class PhoneListView(
    BasePhoneView,
    rw_generics.CreateAPIView
):
    """
    Interface:
    - `POST /contacts/{contact_id}/phone-numbers/`:
      Create a new phone number for the given contact ID.
    """
    pass


class PhoneDetailView(
    BasePhoneView,
    rw_generics.UpdateAPIView,
    generics.DestroyAPIView
):
    """
    Interface:
    - `PUT /contacts/{contact_id}/phone-numbers/{pk}/`:
      Update phone number of the given contact ID.

    - `DELETE /contacts/{contact_id}/phone-numbers/{pk}/`:
      Delete phone number from the given contact ID.
    """
    pass


class BaseMyContactView(rw_generics.GenericAPIView):

    def get_my_contact(self) -> Contact:
        """
        Return `Contact` object belongs to the requester.
        """
        try:
            return Contact.objects.get(user=self.request.user)
        except Contact.DoesNotExist:
            raise Http404

    def get_queryset(self) -> QuerySet[Contact]:
        """
        Returns `Contact` instances belongs to the requester
        with prefetched `phone_numbers` and annotated `starred` data.
        """
        contact = self.get_my_contact()
        return contact.contacts.all().prefetch_phone_numbers()\
            .annotate_starred().order_by('id')

    def get_serializer_context(self) -> Dict:
        """
        We override this method because the write serializer class
        expecting `Contact` object of the requester.
        """
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            context = super().get_serializer_context()
            context.update({'contact': self.get_my_contact()})
            return context

        return super().get_serializer_context()


class MyContactListView(
    BaseMyContactView,
    rw_generics.ListAPIView,
    rw_generics.CreateAPIView
):
    """
    Interface:
    - `GET /contacts/me/contacts/`:
      Get contact list belongs to the requester's contact list.

    - `POST /contacts/me/contacts/`:
      Create a new contact in the requester's contact list.
    """
    write_serializer_class = MyContactCreateDeserializer

    def get_read_serializer_class(self) -> Union[MyContactSerializer, EmptySerializer]:
        if self.request.method == 'GET':
            return MyContactSerializer

        return EmptySerializer


class MyContactDetailView(
    BaseMyContactView,
    rw_generics.RetrieveAPIView,
    rw_generics.UpdateAPIView,
    generics.DestroyAPIView
):
    """
    Interface:
    - `GET /contacts/me/contacts/{pk}/`:
      Retrieve contact from the requester's contact list.
    - `PUT /contacts/me/contacts/{pk}/`:
      Set or unset starred contact in the requester's contact list.
    - `DELETE /contacts/me/contacts/{pk}/`:
      Delete contact from the requester's contact list.
    """
    write_serializer_class = MyContactUpdateDeserializer

    def get_read_serializer_class(self) -> Union[MyContactSerializer, EmptySerializer]:
        if self.request.method == 'GET':
            return MyContactSerializer

        return EmptySerializer

    def perform_destroy(self, instance) -> Response:
        """
        We override this method to delete that `instance`
        from the requester's contact list
        """
        contact = self.get_my_contact()
        contact.contacts.remove(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class BaseGroupView(rw_generics.GenericAPIView):
    read_serializer_class = GroupSerializer
    write_serializer_class = GroupDeserializer

    def get_queryset(self) -> QuerySet[Group]:
        """
        Returns `Group` instances that are accessible for the requester.
        """
        try:
            contact = Contact.objects.get(user=self.request.user)
        except Contact.DoesNotExist:
            raise Http404
        return Group.objects.accessible_for(contact).order_by('id')


class GroupListView(
    BaseGroupView,
    rw_generics.ListAPIView,
    rw_generics.CreateAPIView
):
    """
    Interface:
    - `GET /groups/`: Get contact groups that are accessible to the requester.
    - `POST /groups/`: Create a new contact group.
    """
    pass


class GroupDetailView(
    BaseGroupView,
    rw_generics.RetrieveAPIView,
    rw_generics.UpdateAPIView,
    generics.DestroyAPIView
):
    """
    Interface:
    - `GET /groups/{pk}/`: Retrieve contact group with specific ID.
    - `PUT /groups/{pk}/`: Update contact group with specific ID.
    - `DELETE /groups/{pk}/`: Delete contact group with specific ID.
    """
    pass


class BaseContactGroupView(rw_generics.GenericAPIView):

    def get_group(self) -> Group:
        """
        Return `Group` object of the specific ID given in the URL
        from the requester's `Group` objects.
        """
        try:
            contact = Contact.objects.get(user=self.request.user)
        except Contact.DoesNotExist:
            raise Http404

        try:
            return Group.objects.accessible_for(contact).get(id=self.kwargs['group_id'])
        except Group.DoesNotExist:
            raise Http404

    def get_queryset(self) -> QuerySet[Contact]:
        """
        Returns `Contact` instances that are currently member of the given group ID.
        """
        group = self.get_group()
        return group.get_members()

    def get_serializer_context(self) -> Dict:
        """
        We override this method because the write serializer class
        expecting `Group` object of the given group ID.
        """
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            context = super().get_serializer_context()
            context.update({'group': self.get_group()})
            return context

        return super().get_serializer_context()


class ContactGroupView(
    BaseContactGroupView,
    rw_generics.ListAPIView,
    rw_generics.CreateAPIView
):
    """
    Interface:
    - `GET /groups/{group_id}/contacts/`: Get contact list in the given group ID.
    - `POST /groups/{group_id}/contacts/`: Add contact to the given contact group ID.
    """
    write_serializer_class = ContactGroupCreateDeserializer

    def get_read_serializer_class(self) -> Union[ContactGroupSerializer, EmptySerializer]:
        if self.request.method == 'GET':
            return ContactGroupSerializer

        return EmptySerializer


class ContactGroupDetailView(
    BaseContactGroupView,
    rw_generics.RetrieveAPIView,
    rw_generics.UpdateAPIView,
    generics.DestroyAPIView
):
    """
    Interface:
    - `GET /groups/{group_id}/contacts/{pk}/`: Retrieve contact from the given contact group ID.
    - `UPDATE /groups/{group_id}/contacts/{pk}/`: Update contact in the given contact group ID.
    - `DELETE /groups/{group_id}/contacts/{pk}/`: Delete contact from the given contact group ID.
    """
    write_serializer_class = ContactGroupUpdateDeserializer

    def get_read_serializer_class(self) -> Union[ContactGroupSerializer, EmptySerializer]:
        if self.request.method == 'GET':
            return ContactGroupSerializer

        return EmptySerializer

    def get_permissions(self) -> List[permissions.BasePermission]:
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            self.permission_classes = [permissions.IsAuthenticated, IsGroupAdmin]
        else:
            self.permission_classes = [permissions.IsAuthenticated, IsGroupMember]
        return super().get_permissions()

    def perform_destroy(self, instance) -> Response:
        """
        We override this method to delete that `instance`
        from the the given contact group ID
        """
        group = self.get_group()
        group.contacts.remove(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
