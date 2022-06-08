from django.contrib import admin
from django.contrib.admin import (
    ModelAdmin,
    TabularInline,
    RelatedOnlyFieldListFilter
)
from django.forms import ModelForm

from django_contact.models import (
    Contact,
    ContactMembership
)


class ContactMembershipInline(TabularInline):
    model = ContactMembership
    fk_name = 'owner'
    extra = 0
    fields = (
        'owner',
        'contact',
        'starred',
    )


class ContactForm(ModelForm):
    class Meta:
        model = Contact
        fields = (
            'user',
            'nickname',
            'company',
            'title',
            'address',
            'contacts',
        )


class ContactAdmin(ModelAdmin):
    form = ContactForm
    inlines = (ContactMembershipInline,)
    list_display = (
        'id',
        'user',
        'nickname',
        'company',
        'title',
        'address',
        'created_at',
        'updated_at',
    )
    list_filter = (
        ('user', RelatedOnlyFieldListFilter),
    )
    raw_id_fields = ('user',)
    search_fields = (
        'user__first_name',
        'user__last_name',
    )
    list_per_page = 25


admin.site.register(Contact, ContactAdmin)
