from django.http import Http404
from django.db.models import F, Q, Prefetch
from rest_framework import status
from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    GenericAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView
)
from rest_framework.response import Response

from django_contact.models import (
    Contact,
    Phone,
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


class BaseContactView(GenericAPIView):

    def get_queryset(self):
        """
        Return queryset that contains `Contact` instances
        with prefetched phone numbers.
        """
        prefetch_phone_numbers = Prefetch(
            'phone_numbers',
            Phone.objects.all().annotate(is_primary=F('contactphone__is_primary'))
        )
        return Contact.objects.all()\
            .prefetch_related(prefetch_phone_numbers)\
            .order_by('id')


class ContactListView(BaseContactView, ListAPIView, CreateAPIView):
    """
    Interface:
    - `GET /contacts/`: Get contact list.
    - `POST /contacts/`: Create a new contact.
    """
    serializer_class = ContactSerializer
    deserializer_class = ContactDeserializer

    def list(self, request, *args, **kwargs):
        """
        We override this mixin class's method to use the serializer
        for serializing output.
        """
        context = self.get_serializer_context()
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True, context=context)
            return self.get_paginated_response(serializer.data)

        serializer = self.serializer_class(queryset, many=True, context=context)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        We override this mixin class's method to make use appropriate serializer
        for validating and deserializing input, and for serializing output.
        """
        context = self.get_serializer_context()

        deserializer = self.deserializer_class(data=request.data, context=context)
        deserializer.is_valid(raise_exception=True)
        deserializer.save()

        serializer = self.serializer_class(
            # Repopulate prefetched data of that newly created contact.
            self.get_queryset().get(id=deserializer.instance.id),
            context=context
        )
        headers = self.get_success_headers(serializer.data)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ContactDetailView(
    BaseContactView,
    RetrieveAPIView,
    UpdateAPIView,
    DestroyAPIView
):
    """
    Interface:
    - `GET /contacts/{pk}/`: Retrieve contact with specific ID.
    - `PUT /contacts/{pk}/`: Update contact with specific ID.
    - `DELETE /contacts/{pk}/`: Delete contact with specific ID.
    """
    serializer_class = ContactSerializer
    deserializer_class = ContactDeserializer

    def retrieve(self, request, *args, **kwargs):
        """
        We override this mixin class's method to use the serializer
        for serializing output.
        """
        instance = self.get_object()
        serializer = self.serializer_class(instance, context=self.get_serializer_context())
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """
        We override this mixin class's method to make use appropriate serializer
        for validating and deserializing input, and for serializing output.
        """
        context = self.get_serializer_context()
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        deserializer = self.deserializer_class(instance, data=request.data, partial=partial, context=context)
        deserializer.is_valid(raise_exception=True)
        deserializer.save()

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        serializer = self.serializer_class(
            # Repopulate prefetched data of that updated contact.
            self.get_queryset().get(id=deserializer.instance.id),
            context=context
        )
        return Response(serializer.data)


class BaseContactOfContactView(GenericAPIView):

    def get_queryset(self):
        """
        Narrows down `self` queryset to the `Contact` instances
        that belongs to the specific contact.
        """
        try:
            contact = Contact.objects.get(id=self.kwargs['contact_id'])
        except Contact.DoesNotExist:
            raise Http404

        # Prefetch contacts' phone numbers
        prefetch_phone_numbers = Prefetch(
            'phone_numbers',
            Phone.objects.all().annotate(is_primary=F('contactphone__is_primary'))
        )

        return contact.contacts.all()\
            .prefetch_related(prefetch_phone_numbers)\
            .annotate(starred=F('contactmembership__starred'))\
            .order_by('id')


class ContactOfContactListView(
    BaseContactOfContactView,
    ListAPIView,
    CreateAPIView
):
    """
    Interface:
    - `GET /contacts/{contact_id}/contact-list/`: Get contact list
      belongs to the given contact ID.

    - `POST /contacts/{contact_id}/contact-list/`: Create a new contact
      in the contact list of the given contact ID.
    """
    serializer_class = ContactOfContactSerializer
    deserializer_class = ContactOfContactDeserializer

    def list(self, request, *args, **kwargs):
        """
        We override this mixin class's method to use the serializer
        for serializing output.
        """
        context = self.get_serializer_context()
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True, context=context)
            return self.get_paginated_response(serializer.data)

        serializer = self.serializer_class(queryset, many=True, context=context)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        We override this mixin class's method to make use appropriate serializer
        for validating and deserializing input, and for serializing output.
        """
        try:
            contact = Contact.objects.get(id=self.kwargs['contact_id'])
        except Contact.DoesNotExist:
            raise Http404

        context = self.get_serializer_context()
        context.update({'contact': contact})

        deserializer = self.deserializer_class(data=request.data, context=context)
        deserializer.is_valid(raise_exception=True)
        deserializer.save()

        serializer = self.serializer_class(
            # Repopulate prefetched and preselected data
            # of that newly created contact.
            self.get_queryset().get(id=deserializer.instance.id),
            context=context
        )
        headers = self.get_success_headers(serializer.data)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ContactOfContactDetailView(
    BaseContactOfContactView,
    RetrieveAPIView,
    DestroyAPIView
):
    """
    Interface:
    - `GET /contacts/{contact_id}/contact-list/{pk}/`: Retrieve contact
      from the contact list of the given contact ID.

    - `DELETE /contacts/{contact_id}/contact-list/{pk}/`: Delete contact
      from the contact list of the given contact ID.
    """
    serializer_class = ContactOfContactSerializer

    def retrieve(self, request, *args, **kwargs):
        """
        We override this mixin class's method to use the serializer
        for serializing output.
        """
        instance = self.get_object()
        serializer = self.serializer_class(instance, context=self.get_serializer_context())
        return Response(serializer.data)

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


class BaseContactPhoneNumberView(GenericAPIView):

    def get_queryset(self):
        """
        Narrows down `self` queryset to the `Contact` instances
        that belongs to the specific contact.
        """
        try:
            contact = Contact.objects.get(id=self.kwargs['contact_id'])
        except Contact.DoesNotExist:
            raise Http404

        return contact.phone_numbers.all()\
            .annotate(is_primary=F('contactphone__is_primary'))


class ContactPhoneNumberListView(
    BaseContactPhoneNumberView,
    CreateAPIView
):
    """
    Interface:
    - `POST /contacts/{contact_id}/phone-numbers/`: Create a new phone number
      for the given contact ID.
    """
    serializer_class = PhoneSerializer
    deserializer_class = PhoneDeserializer

    def create(self, request, *args, **kwargs):
        """
        We override this mixin class's method to make use appropriate serializer
        for validating and deserializing input, and for serializing output.
        """
        try:
            contact = Contact.objects.get(id=self.kwargs['contact_id'])
        except Contact.DoesNotExist:
            raise Http404

        context = self.get_serializer_context()
        context.update({'contact': contact})

        deserializer = self.deserializer_class(data=request.data, context=context)
        deserializer.is_valid(raise_exception=True)
        deserializer.save()

        serializer = self.serializer_class(
            # Repopulate preselected data
            # of that newly created phone number.
            self.get_queryset().get(id=deserializer.instance.id),
            context=context
        )
        headers = self.get_success_headers(serializer.data)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ContactPhoneNumberDetailView(
    BaseContactPhoneNumberView,
    UpdateAPIView,
    DestroyAPIView
):
    """
    Interface:
    - `PUT /contacts/{contact_id}/phone-numbers/{pk}/`: Update phone number
      of the given contact ID.

    - `DELETE /contacts/{contact_id}/phone-numbers/{pk}/`: Delete phone number
      from the given contact ID.
    """
    serializer_class = PhoneSerializer
    deserializer_class = PhoneDeserializer

    def update(self, request, *args, **kwargs):
        """
        We override this mixin class's method to make use appropriate serializer
        for validating and deserializing input, and for serializing output.
        """
        try:
            contact = Contact.objects.get(id=self.kwargs['contact_id'])
        except Contact.DoesNotExist:
            raise Http404

        context = self.get_serializer_context()
        context.update({'contact': contact})

        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        deserializer = self.deserializer_class(instance, data=request.data, partial=partial, context=context)
        deserializer.is_valid(raise_exception=True)
        deserializer.save()

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        serializer = self.serializer_class(
            # Repopulate preselected data
            # of that newly created phone number.
            self.get_queryset().get(id=deserializer.instance.id),
            context=context
        )
        return Response(serializer.data)


class BaseContactGroupView(GenericAPIView):

    def get_queryset(self):
        """
        Returns union of `Group` instances:
        - Groups created by the requester.
        - Groups where the requester is a member of.
        """
        # TODO: Change the `Group.created_by` field's type with foreign key to `Contact` instead of user
        # TODO: Change the `Group.updated_by` field's type with foreign key to `Contact` instead of user
        return Group.objects.filter(
            Q(created_by=self.request.user) | Q(contactgroup__contact__user=self.request.user)
        ).distinct().order_by('id')


class GroupListView(
    BaseContactGroupView,
    ListAPIView,
    CreateAPIView
):
    """
    Interface:
    - `GET /groups/`: Get contact groups that can be accessed by the requester.
    - `POST /groups/`: Create a new contact group.
    """
    serializer_class = GroupSerializer
    deserializer_class = GroupDeserializer

    def list(self, request, *args, **kwargs):
        """
        We override this mixin class's method to use the serializer
        for serializing output.
        """
        context = self.get_serializer_context()
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True, context=context)
            return self.get_paginated_response(serializer.data)

        serializer = self.serializer_class(queryset, many=True, context=context)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        We override this mixin class's method to make use appropriate serializer
        for validating and deserializing input, and for serializing output.
        """
        context = self.get_serializer_context()

        deserializer = self.deserializer_class(data=request.data, context=context)
        deserializer.is_valid(raise_exception=True)
        deserializer.save()

        serializer = self.serializer_class(deserializer.instance, context=context)
        headers = self.get_success_headers(serializer.data)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class GroupDetailView(
    BaseContactGroupView,
    RetrieveAPIView,
    UpdateAPIView,
    DestroyAPIView
):
    """
    Interface:
    - `GET /groups/{pk}/`: Retrieve contact group with specific ID.
    - `PUT /groups/{pk}/`: Update contact group with specific ID.
    - `DELETE /groups/{pk}/`: Delete contact group with specific ID.
    """
    serializer_class = GroupSerializer
    deserializer_class = GroupDeserializer

    def retrieve(self, request, *args, **kwargs):
        """
        We override this mixin class's method to use the serializer
        for serializing output.
        """
        instance = self.get_object()
        serializer = self.serializer_class(instance, context=self.get_serializer_context())
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """
        We override this mixin class's method to make use appropriate serializer
        for validating and deserializing input, and for serializing output.
        """
        context = self.get_serializer_context()
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        deserializer = self.deserializer_class(instance, data=request.data, partial=partial, context=context)
        deserializer.is_valid(raise_exception=True)
        deserializer.save()

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        serializer = self.serializer_class(deserializer.instance, context=context)
        return Response(serializer.data)


class BaseContactGroupView(GenericAPIView):

    def get_queryset(self):
        """
        Returns union of `Group` instances:
        - Groups created by the requester.
        - Groups where the requester is a contact of.
        """
        # TODO: Change the `Group.created_by` field's type with foreign key to `Contact` instead of user
        # TODO: Change the `Group.updated_by` field's type with foreign key to `Contact` instead of user
        return Group.objects.filter(
            Q(created_by=self.request.user) | Q(contactgroup__contact__user=self.request.user)
        )

    def get_contacts_of(self, group):
        """
        Returns `Contact` queryset associated with the given contact `group`
        with (`role`, `invited_by`, `joined_at`) fields are annotated from the `ContactGroup`
        """
        prefetch_phone_numbers = Prefetch(
            'phone_numbers',
            Phone.objects.all().annotate(is_primary=F('contactphone__is_primary'))
        )
        return group.contacts.all()\
            .prefetch_related(prefetch_phone_numbers)\
            .annotate(role=F('contactgroup__role'))\
            .annotate(invited_by=F('contactgroup__inviter'))\
            .annotate(joined_at=F('contactgroup__joined_at'))\
            .order_by('id').distinct()


class ContactGroupView(
    BaseContactGroupView,
    ListAPIView,
    CreateAPIView
):
    """
    Interface:
    - `GET /groups/{group_id}/contacts/`: Get contact list from the given group ID.
    - `POST /groups/{group_id}/contacts/`: Add contact to the given contact group ID.
    """
    serializer_class = ContactGroupSerializer
    deserializer_class = ContactGroupDeserializer

    def get_queryset(self):
        """
        Returns `Contact` queryset associated with the given contact group ID.
        """
        groups = super().get_queryset()
        try:
            group = groups.get(id=self.kwargs['group_id'])
        except Contact.DoesNotExist:
            raise Http404

        return self.get_contacts_of(group)

    def list(self, request, *args, **kwargs):
        """
        We override this mixin class's method to use the serializer
        for serializing output.
        """
        context = self.get_serializer_context()
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True, context=context)
            return self.get_paginated_response(serializer.data)

        serializer = self.serializer_class(queryset, many=True, context=context)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        We override this mixin class's method to make use appropriate serializer
        for validating and deserializing input, and for serializing output.
        """
        try:
            group = super().get_queryset().get(id=self.kwargs['group_id'])
        except Group.DoesNotExist:
            raise Http404

        context = self.get_serializer_context()
        context.update({'group': group})

        deserializer = self.deserializer_class(data=request.data, context=context)
        deserializer.is_valid(raise_exception=True)
        deserializer.save()

        serializer = self.serializer_class(
            # Repopulate prefetched data of that newly added contact.
            self.get_queryset().get(id=deserializer.instance.id),
            context=context
        )
        headers = self.get_success_headers(serializer.data)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ContactGroupDetailView(
    BaseContactGroupView,
    RetrieveAPIView,
    UpdateAPIView,
    DestroyAPIView
):
    """
    Interface:
    - `GET /groups/{group_id}/contacts/{pk}/`: Retrieve contact from the given contact group ID.
    - `UPDATE /groups/{group_id}/contacts/{pk}/`: Update contact in the given contact group ID.
    - `DELETE /groups/{group_id}/contacts/{pk}/`: Delete contact from the given contact group ID.
    """
    serializer_class = ContactGroupSerializer
    deserializer_class = ContactGroupDeserializer

    def get_queryset(self):
        """
        Returns `Contact` queryset associated with the given contact group ID.
        """
        groups = super().get_queryset()
        try:
            group = groups.get(id=self.kwargs['group_id'])
        except Group.DoesNotExist:
            raise Http404

        return self.get_contacts_of(group)

    def retrieve(self, request, *args, **kwargs):
        """
        We override this mixin class's method to use the serializer
        for serializing output.
        """
        instance = self.get_object()
        serializer = self.serializer_class(instance, context=self.get_serializer_context())
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """
        We override this mixin class's method to make use appropriate serializer
        for validating and deserializing input, and for serializing output.
        """
        try:
            group = super().get_queryset().get(id=self.kwargs['group_id'])
        except Group.DoesNotExist:
            raise Http404

        context = self.get_serializer_context()
        context.update({'group': group})

        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        deserializer = self.deserializer_class(instance, data=request.data, partial=partial, context=context)
        deserializer.is_valid(raise_exception=True)
        deserializer.save()

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        serializer = self.serializer_class(deserializer.instance, context=context)
        return Response(serializer.data)

    def perform_destroy(self, instance):
        """
        We override this method to delete that `instance`
        from the the given contact group ID
        """
        try:
            group = self.get_queryset().get(id=self.kwargs['group_id'])
        except Group.DoesNotExist:
            raise Http404

        group.contacts.remove(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
