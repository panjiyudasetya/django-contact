from django.urls import path

from django_contact.views import (
    ContactView,
    ContactDetailView,
    ContactOfContactListView,
    ContactOfContactDetailView
)

urlpatterns = [
    path('contacts/',
         ContactView.as_view(),
         name='contacts'),
    path('contacts/<int:pk>/',
         ContactDetailView.as_view(),
         name='contacts-detail'),

    path('contacts/<int:contact_id>/contact-list/',
         ContactOfContactListView.as_view(),
         name='contacts-of-contact'),
    path('contacts/<int:contact_id>/contact-list/<int:pk>/',
         ContactOfContactDetailView.as_view(),
         name='contacts-of-contact-detail'),
]
