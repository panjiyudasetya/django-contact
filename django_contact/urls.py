from django.urls import path

from django_contact.views import (
    AllContactView,
    ContactListView,
    ContactListDetailView
)

urlpatterns = [
    path('contacts/',
         AllContactView.as_view(),
         name='contacts'),

    path('contacts/<int:id>/contacts/',
         ContactListView.as_view(),
         name='contacts-of-contact'),

    path('contacts/<int:id>/contacts/<int:contact_id>/',
         ContactListDetailView.as_view(),
         name='contacts-of-contact-detail'),
]
