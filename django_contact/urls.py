from django.urls import path

from django_contact.views import ContactListView

urlpatterns = [
    path('contacts/', ContactListView.as_view(), name='contacts'),
]
