from django.urls import path

from django_contact.views import (
    ContactListView,
    ContactListDetailView
)

urlpatterns = [
    path('contacts/',
         ContactListView.as_view(),
         name='contacts'),

    path('contacts/<int:contact_id>/contacts/',
         ContactListDetailView.as_view(),
         name='contacts-of-contact'),
]
