from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import as_serializer_error
from typing import Dict, List

from django_contact.models import (
    Contact,
    Phone,
    ContactPhone
)


User = get_user_model()


class ContactSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    email = serializers.EmailField(source='user.email')
    phone_numbers = serializers.SerializerMethodField()

    class Meta:
        model = Contact
        fields = (
            'id',
            'first_name',
            'last_name',
            'nickname',
            'email',
            'company',
            'title',
            'phone_numbers',
            'address',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields

    def get_phone_numbers(self, obj):
        # Assuming that `obj` comes with
        # prefetched `phone_numbers` attribute
        return [
            {
                'phone_number': {
                    'id': p.id,
                    'number': p.phone_number.national_number,
                    'country_code': p.phone_number.country_code,
                    'country_code_source': p.phone_number.country_code_source
                },
                'type': p.phone_type,
                'is_primary': p.is_primary,
                'created_at': p.created_at,
                'updated_at': p.updated_at
            }
            for p in obj._prefetched_objects_cache['phone_numbers']
        ]


class ContactDeserializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        required=False,
        queryset=User.objects.all()
    )

    class Meta:
        model = Contact
        fields = (
            'user',
            'nickname',
            'company',
            'title',
            'address',
        )

    def update(self, instance, validated_data):
        # The `user` field should never be modified on update
        # Therefore, we need to remove it from the `validated_data` object
        validated_data.pop('user', None)
        return super().update(instance, validated_data)


class ContactOfContactSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    email = serializers.EmailField(source='user.email')
    phone_numbers = serializers.SerializerMethodField()
    starred = serializers.SerializerMethodField()

    class Meta:
        model = Contact
        fields = (
            'id',
            'first_name',
            'last_name',
            'nickname',
            'email',
            'company',
            'title',
            'phone_numbers',
            'address',
            'created_at',
            'updated_at',
            'starred',
        )
        read_only_fields = fields

    def get_phone_numbers(self, obj) -> List[Dict]:
        # Assuming that `obj` comes with
        # prefetched `phone_numbers` attribute
        return [
            {
                'phone_number': {
                    'id': p.id,
                    'number': p.phone_number.national_number,
                    'country_code': p.phone_number.country_code,
                    'country_code_source': p.phone_number.country_code_source
                },
                'type': p.phone_type,
                'is_primary': p.is_primary,
                'created_at': p.created_at,
                'updated_at': p.updated_at
            }
            for p in obj._prefetched_objects_cache['phone_numbers']
        ]

    def get_starred(self, obj) -> bool:
        # Assuming that `obj` comes with
        # preselected `starred` attribute
        return obj.starred


class ContactOfContactDeserializer(serializers.Serializer):
    contact = serializers.PrimaryKeyRelatedField(
        queryset=Contact.objects.all()
    )
    starred = serializers.BooleanField(default=False)

    class Meta:
        fields = ('contact', 'starred',)

    @transaction.atomic
    def create(self, validated_data):
        new_contact = validated_data.get('contact')
        starred = validated_data.get('starred')

        # Assuming the serializer's context comes with the `contact` object
        contact = self.context.get('contact')
        contact.contacts.add(new_contact, through_defaults={'starred': starred})

        # Set contact favorite indicator as the contact's attribute
        setattr(new_contact, 'starred', starred)

        return new_contact


class PhoneSerializer(serializers.ModelSerializer):
    phone_number = serializers.SerializerMethodField()
    is_primary = serializers.SerializerMethodField()

    class Meta:
        model = Phone
        fields = (
            'id',
            'phone_number',
            'phone_type',
            'is_primary',
        )
        read_only_fields = fields

    def get_phone_number(self, obj):
        return {
            'number': obj.phone_number.national_number,
            'country_code': obj.phone_number.country_code,
            'country_code_source': obj.phone_number.country_code_source
        }

    def get_is_primary(self, obj):
        # Assuming that `obj` comes with `is_primary` attribute
        return obj.is_primary


class PhoneDeserializer(serializers.ModelSerializer):
    is_primary = serializers.BooleanField(required=False)

    class Meta:
        model = Phone
        fields = (
            'phone_number',
            'phone_type',
            'is_primary',
        )

    @transaction.atomic
    def save(self, **kwargs) -> None:
        """
        We override this method to update or create `ContactPhone` object
        associated with the `Contact` and `Phone` instances.
        """
        is_primary = self.validated_data.pop('is_primary')
        super().save(**kwargs)

        # Assuming the serializer's context comes with the `contact` object
        contact = self.context.get('contact')
        self._validate_contact_phone(contact, self.instance, is_primary)

        # Update or create the `Phone` instance
        # that belongs to the `contact` object
        ContactPhone.objects.update_or_create(
            contact=contact,
            phone=self.instance,
            defaults={'is_primary': is_primary}
        )

    def _validate_contact_phone(self, contact, phone, is_primary) -> None:
        try:
            ContactPhone(
                contact=contact,
                phone=phone,
                is_primary=is_primary
            ).clean()
        except DjangoValidationError as err:
            raise ValidationError(detail=as_serializer_error(err))
