from django.http import Http404
from django.db.models import F
from rest_framework.generics import ListAPIView

from django_contact.models import Contact
from django_contact.serializers import ContactSerializer


class ContactListView(ListAPIView):
    serializer_class = ContactSerializer

    def get_queryset(self):
        """
        Narrows down `self` queryset to the Contact objects
        that belongs to the requester.
        """
        try:
            contact = Contact.objects.first()
        except Contact.DoesNotExist:
            raise Http404

        return contact.contacts.all()\
            .annotate(starred=F('contactmembership__starred'))
