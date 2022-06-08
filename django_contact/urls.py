from django.urls import path

from django_contact.views import (
    ContactListView,
    ContactDetailView,
    PhoneListView,
    PhoneDetailView,
    MyContactListView,
    MyContactDetailView,
    GroupListView,
    GroupDetailView,
    ContactGroupView,
    ContactGroupDetailView
)

urlpatterns = [
    path('contacts/',
         ContactListView.as_view(),
         name='contacts'),
    path('contacts/<int:pk>/',
         ContactDetailView.as_view(),
         name='contacts-detail'),

    path('contacts/<int:contact_id>/phone-numbers/',
         PhoneListView.as_view(),
         name='contacts-detail'),
    path('contacts/<int:contact_id>/phone-numbers/<int:pk>/',
         PhoneDetailView.as_view(),
         name='contacts-detail'),

    path('contacts/me/contacts/',
         MyContactListView.as_view(),
         name='contacts-me-contacts'),
    path('contacts/me/contacts/<int:pk>/',
         MyContactDetailView.as_view(),
         name='contacts-me-contacts-detail'),

    path('groups/',
         GroupListView.as_view(),
         name='groups'),
    path('groups/<int:pk>/',
         GroupDetailView.as_view(),
         name='groups-detail'),

    path('groups/<int:group_id>/contacts/',
         ContactGroupView.as_view(),
         name='groups-contacts'),
    path('groups/<int:group_id>/contacts/<int:pk>/',
         ContactGroupDetailView.as_view(),
         name='groups-contacts-detail'),
]
