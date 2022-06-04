from django.http import Http404
from django.db.models import F, Prefetch
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
    Phone
)
from django_contact.serializers import (
    ContactSerializer,
    ContactDeserializer,
    ContactOfContactSerializer,
    ContactOfContactDeserializer,
    PhoneSerializer,
    PhoneDeserializer
)


class BaseContactView(GenericAPIView):

    def get_queryset(self):
        """
        Return queryset that contains Contact instances
        with prefetched phone numbers.
        """
        prefetch_phone_numbers = Prefetch(
            'phone_numbers',
            Phone.objects.all().annotate(is_primary=F('contactphone__is_primary'))
        )
        return Contact.objects.all().prefetch_related(prefetch_phone_numbers)\
            .order_by('id')


class ContactView(BaseContactView, ListAPIView, CreateAPIView):
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
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        We override this mixin class's method to make use appropriate serializer
        for validating and deserializing input, and for serializing output.
        """
        deserializer = self.deserializer_class(data=request.data)
        deserializer.is_valid(raise_exception=True)
        deserializer.save()

        serializer = self.serializer_class(
            # Repopulate prefetched data of that newly created contact.
            self.get_queryset().get(id=deserializer.instance.id)
        )
        headers = self.get_success_headers(serializer.data)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ContactDetailView(BaseContactView, RetrieveAPIView, UpdateAPIView, DestroyAPIView):
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
        serializer = self.serializer_class(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """
        We override this mixin class's method to make use appropriate serializer
        for validating and deserializing input, and for serializing output.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        deserializer = self.deserializer_class(instance, data=request.data, partial=partial)
        deserializer.is_valid(raise_exception=True)
        deserializer.save()

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        serializer = self.serializer_class(
            # Repopulate prefetched data of that updated contact.
            self.get_queryset().get(id=deserializer.instance.id)
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
            .annotate(starred=F('contactmembership__starred'))


class ContactOfContactListView(BaseContactOfContactView, ListAPIView, CreateAPIView):
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
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.serializer_class(queryset, many=True)
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

        deserializer = self.deserializer_class(data=request.data)
        deserializer.context.update({'contact': contact})
        deserializer.is_valid(raise_exception=True)
        deserializer.save()

        serializer = self.serializer_class(
            # Repopulate prefetched and preselected data
            # of that newly created contact.
            self.get_queryset().get(id=deserializer.instance.id)
        )
        headers = self.get_success_headers(serializer.data)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ContactOfContactDetailView(BaseContactOfContactView, RetrieveAPIView, DestroyAPIView):
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
        serializer = self.serializer_class(instance)
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
