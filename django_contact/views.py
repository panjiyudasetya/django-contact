from django.http import Http404
from django.db.models import F, Prefetch
from rest_framework.generics import (
    GenericAPIView,
    ListAPIView
)

from django_contact.models import (
    Contact,
    Phone
)
from django_contact.serializers import (
    ContactSerializer,
    ContactListDetailSerializer
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


class ContactListView(BaseContactView, ListAPIView):
    """
    Interface:
    - `GET /contacts/` : List all `Contact` instances.
    """
    serializer_class = ContactSerializer


class ContactListDetailView(BaseContactView, ListAPIView):
    """
    Interface:
    - `GET /contacts/{contact_id}/contacts/` : List all `Contact` instances
      of the given contact ID.
    """
    serializer_class = ContactListDetailSerializer

    def get_queryset(self):
        """
        Narrows down `self` queryset to the Contact objects
        that belongs to the requester.
        """
        try:
            contact = super().get_queryset()\
                .get(id=self.kwargs['contact_id'])
        except Contact.DoesNotExist:
            raise Http404

        # Prefetch contacts' phone numbers that are belongs to the `contact` object
        prefetch_phone_numbers = Prefetch(
            'phone_numbers',
            Phone.objects.all().annotate(is_primary=F('contactphone__is_primary'))
        )
        return contact.contacts.all()\
            .prefetch_related(prefetch_phone_numbers)\
            .annotate(starred=F('contactmembership__starred'))
