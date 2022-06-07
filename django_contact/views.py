from django.http import Http404
from drf_rw_serializers import generics as rw_generics
from rest_framework import status, generics
from rest_framework.response import Response

from django_contact.models import (
    Contact,
    Group
)
from django_contact.serializers import (
    ContactSerializer,
    ContactDeserializer,
    ContactOfContactSerializer,
    ContactOfContactDeserializer,
    PhoneSerializer,
    PhoneDeserializer,
    GroupSerializer,
    GroupDeserializer,
    ContactGroupSerializer,
    ContactGroupDeserializer,
)


class BaseContactView(rw_generics.GenericAPIView):
    read_serializer_class = ContactSerializer
    write_serializer_class = ContactDeserializer

    def get_queryset(self):
        """
        Returns all `Contact` instances with prefetched `phone_numbers`.
        """
        return Contact.objects.all().prefetch_phone_numbers().order_by('id')


class ContactListView(
    BaseContactView,
    rw_generics.ListAPIView,
    rw_generics.CreateAPIView
):
    """
    Interface:
    - `GET /contacts/`: Get contact list.
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


class BaseContactPhoneNumberView(rw_generics.GenericAPIView):
    read_serializer_class = PhoneSerializer
    write_serializer_class = PhoneDeserializer

    def get_serializer_context(self):
        """
        We override this method because the write serializer class
        expecting `Contact` object of the given contact ID.
        """
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            try:
                contact = Contact.objects.get(id=self.kwargs['contact_id'])
            except Contact.DoesNotExist:
                raise Http404

            context = super().get_serializer_context()
            context.update({'contact': contact})
            return context

        return super().get_serializer_context()

    def get_queryset(self):
        """
        Returns `Phone` instances belongs to the given contact ID
        with annotated `is_primary` data.
        """
        try:
            contact = Contact.objects.get(id=self.kwargs['contact_id'])
        except Contact.DoesNotExist:
            raise Http404

        return contact.phone_numbers.all().annotate_is_primary().order_by('id')


class ContactPhoneNumberListView(
    BaseContactPhoneNumberView,
    rw_generics.CreateAPIView
):
    """
    Interface:
    - `POST /contacts/{contact_id}/phone-numbers/`:
      Create a new phone number for the given contact ID.
    """
    pass


class ContactPhoneNumberDetailView(
    BaseContactPhoneNumberView,
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


class BaseContactOfContactView(rw_generics.GenericAPIView):
    read_serializer_class = ContactOfContactSerializer
    write_serializer_class = ContactOfContactDeserializer

    def get_serializer_context(self):
        """
        We override this method because the write serializer class
        expecting `Contact` object of the given contact ID.
        """
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            try:
                contact = Contact.objects.get(id=self.kwargs['contact_id'])
            except Contact.DoesNotExist:
                raise Http404

            context = super().get_serializer_context()
            context.update({'contact': contact})
            return context

        return super().get_serializer_context()

    def get_queryset(self):
        """
        Returns `Contact` instances belongs to the given contact ID
        with prefetched `phone_numbers` and annotated `starred` data.
        """
        try:
            contact = Contact.objects.get(id=self.kwargs['contact_id'])
        except Contact.DoesNotExist:
            raise Http404

        return contact.contacts.all().prefetch_phone_numbers()\
            .annotate_starred().order_by('id')


class ContactOfContactListView(
    BaseContactOfContactView,
    rw_generics.ListAPIView,
    rw_generics.CreateAPIView
):
    """
    Interface:
    - `GET /contacts/{contact_id}/contact-list/`:
      Get contact list belongs to the given contact ID.

    - `POST /contacts/{contact_id}/contact-list/`:
      Create a new contact in the contact list of the given contact ID.
    """
    pass


class ContactOfContactDetailView(
    BaseContactOfContactView,
    rw_generics.RetrieveAPIView,
    generics.DestroyAPIView
):
    """
    Interface:
    - `GET /contacts/{contact_id}/contact-list/{pk}/`:
      Retrieve contact from the contact list of the given contact ID.

    - `DELETE /contacts/{contact_id}/contact-list/{pk}/`:
      Delete contact from the contact list of the given contact ID.
    """
    serializer_class = ContactOfContactSerializer

    def perform_destroy(self, instance):
        """
        We override this method to delete that `instance`
        from the contact list belongs the given contact ID
        """
        try:
            contact = Contact.objects.get(id=self.kwargs['contact_id'])
        except Contact.DoesNotExist:
            raise Http404

        contact.contacts.remove(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class BaseGroupView(rw_generics.GenericAPIView):
    read_serializer_class = GroupSerializer
    write_serializer_class = GroupDeserializer

    def get_queryset(self):
        """
        Returns `Group` instances that are accessible for the given contact ID.
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
    - `GET /groups/`: Get contact groups that are accessible for the requester.
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
    read_serializer_class = ContactGroupSerializer
    write_serializer_class = ContactGroupDeserializer

    def get_serializer_context(self):
        """
        We override this method because the write serializer class
        expecting `Group` object of the given group ID.
        """
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            try:
                group = self.get_contact_groups().get(id=self.kwargs['group_id'])
            except Group.DoesNotExist:
                raise Http404

            context = super().get_serializer_context()
            context.update({'group': group})
            return context

        return super().get_serializer_context()

    def get_contact_groups(self):
        """
        Returns `Group` instances that are accessible for the given contact ID.
        """
        try:
            contact = Contact.objects.get(user=self.request.user)
        except Contact.DoesNotExist:
            raise Http404

        return Group.objects.accessible_for(contact).order_by('id')

    def get_queryset(self):
        """
        Returns `Contact` instances that are currently member of the given group ID.
        """
        groups = self.get_contact_groups()
        try:
            group = groups.get(id=self.kwargs['group_id'])
        except Group.DoesNotExist:
            raise Http404

        return group.get_contacts()


class ContactGroupView(
    BaseContactGroupView,
    rw_generics.ListAPIView,
    rw_generics.CreateAPIView
):
    """
    Interface:
    - `GET /groups/{group_id}/contacts/`: Get contact list from the given group ID.
    - `POST /groups/{group_id}/contacts/`: Add contact to the given contact group ID.
    """
    pass


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

    def perform_destroy(self, instance):
        """
        We override this method to delete that `instance`
        from the the given contact group ID
        """
        try:
            group = super().get_contact_groups().get(id=self.kwargs['group_id'])
        except Group.DoesNotExist:
            raise Http404

        group.contacts.remove(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
