from django.http import Http404
from django.db.models import F, Prefetch
from rest_framework import status
from rest_framework.generics import (
    GenericAPIView,
    ListAPIView,
    RetrieveAPIView,
    DestroyAPIView
)
from rest_framework.response import Response

from django_contact.models import (
    Contact,
    Phone
)
from django_contact.serializers import (
    ContactSerializer,
    ContactDetailSerializer
)


class AllContactView(ListAPIView):
    """
    Interface:
    - GET /contacts/
      Get all contact
    """
    serializer_class = ContactSerializer

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


class BaseContactView(GenericAPIView):

    def get_queryset(self):
        """
        Narrows down `self` queryset to the `Contact` instances
        that belongs to the specific contact.
        """
        try:
            contact = Contact.objects.get(id=self.kwargs['id'])
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


class ContactListView(BaseContactView, ListAPIView):
    """
    Interface:
    - GET /contacts/{id}/contacts/
      Get contact list belongs to the given contact ID.
    """
    serializer_class = ContactDetailSerializer


class ContactListDetailView(
    BaseContactView,
    RetrieveAPIView,
    DestroyAPIView
):
    """
    Interface:
    - GET /contacts/{id}/contacts/{contact_id}/
      Retrieve contact list belongs to the given contact ID.
    """
    serializer_class = ContactDetailSerializer

    lookup_url_kwarg = 'contact_id'
    lookup_field = 'pk'

    def perform_destroy(self, instance):
        """
        We override this method to delete that `instance`
        from the contact list belongs the given contact ID
        """
        try:
            contact = Contact.objects.get(id=self.kwargs['id'])
        except Contact.DoesNotExist:
            raise Http404
        
        contact.contacts.remove(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
