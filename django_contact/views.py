from django.http import Http404
from rest_framework.generics import ListAPIView

from django_contact.models import Contact


class ContactListView(ListAPIView):

    def get_queryset(self):
        """
        Narrows down `self` queryset to the Contact objects
        that belongs to the requester.
        """
        try:
            contact = Contact.objects.get(user=self.request.user)
        except Contact.DoesNotExist:
            raise Http404

        return contact.contacts.all()
