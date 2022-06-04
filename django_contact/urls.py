from django.urls import path

from django_contact.views import (
    ContactListView,
    ContactDetailView,
    ContactPhoneNumberListView,
    ContactPhoneNumberDetailView,
    ContactOfContactListView,
    ContactOfContactDetailView,
    GroupListView,
    GroupDetailView,
    GroupMembershipView,
    GroupMembershipDetailView
)

urlpatterns = [
    path('contacts/',
         ContactListView.as_view(),
         name='contacts'),
    path('contacts/<int:pk>/',
         ContactDetailView.as_view(),
         name='contacts-detail'),

    path('contacts/<int:contact_id>/phone-numbers/',
         ContactPhoneNumberListView.as_view(),
         name='contacts-detail'),
    path('contacts/<int:contact_id>/phone-numbers/<int:pk>/',
         ContactPhoneNumberDetailView.as_view(),
         name='contacts-detail'),

    path('contacts/<int:contact_id>/contact-list/',
         ContactOfContactListView.as_view(),
         name='contacts-of-contact'),
    path('contacts/<int:contact_id>/contact-list/<int:pk>/',
         ContactOfContactDetailView.as_view(),
         name='contacts-of-contact-detail'),

    path('groups/',
         GroupListView.as_view(),
         name='groups'),
    path('groups/<int:pk>/',
         GroupDetailView.as_view(),
         name='groups-detail'),

    path('groups/<int:group_id>/members/',
         GroupMembershipView.as_view(),
         name='groups-members'),
    path('groups/<int:group_id>/members/<int:pk>/',
         GroupMembershipDetailView.as_view(),
         name='groups-members-detail'),
]
