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
    ContactPhone,
    Group,
    ContactGroup
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

    def get_phone_numbers(self, obj) -> List[Dict]:
        # Assuming that `obj` comes with
        # prefetched `phone_numbers` attribute
        return [
            {
                'id': p.id,
                'phone_number': {
                    'value': p.phone_number.national_number,
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

    def update(self, instance, validated_data) -> Contact:
        # The `user` field should never be modified on update
        # Therefore, we need to remove it from the `validated_data` object
        validated_data.pop('user', None)
        return super().update(instance, validated_data)


class ContactOfContactSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    email = serializers.EmailField(source='user.email')
    phone_numbers = serializers.SerializerMethodField()
    # Assuming the `serializer.instance` comes with preselected `starred` field
    starred = serializers.BooleanField()

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
                'id': p.id,
                'phone_number': {
                    'value': p.phone_number.national_number,
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


class ContactOfContactDeserializer(serializers.Serializer):
    contact = serializers.PrimaryKeyRelatedField(
        queryset=Contact.objects.all()
    )
    starred = serializers.BooleanField(default=False)

    class Meta:
        fields = ('contact', 'starred',)

    @transaction.atomic
    def create(self, validated_data) -> Contact:
        new_contact = validated_data.get('contact')
        starred = validated_data.get('starred')

        # Assuming the serializer's context comes with the `contact` object
        contact = self.context.get('contact')
        contact.contacts.add(new_contact, through_defaults={'starred': starred})

        return new_contact


class PhoneSerializer(serializers.ModelSerializer):
    phone_number = serializers.SerializerMethodField()
    # Assuming the `serializer.instance` comes with preselected `is_primary` field
    is_primary = serializers.BooleanField()

    class Meta:
        model = Phone
        fields = (
            'id',
            'phone_number',
            'phone_type',
            'is_primary',
        )
        read_only_fields = fields

    def get_phone_number(self, obj) -> Dict:
        return {
            'number': obj.phone_number.national_number,
            'country_code': obj.phone_number.country_code,
            'country_code_source': obj.phone_number.country_code_source
        }


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
    def save(self, **kwargs) -> Phone:
        """
        We override this method to update or create `ContactPhone` object
        associated with the `Contact` and `Phone` instances.
        """
        is_primary = self.validated_data.pop('is_primary')
        instance = super().save(**kwargs)

        # Assuming the serializer's context comes with the `contact` object
        contact = self.context.get('contact')
        self._validate_contact_phone(contact, instance, is_primary)

        # Update or create the `Phone` instance
        # that belongs to the `contact` object
        ContactPhone.objects.update_or_create(
            contact=contact,
            phone=instance,
            defaults={'is_primary': is_primary}
        )

        return instance

    def _validate_contact_phone(self, contact, phone, is_primary) -> None:
        try:
            ContactPhone(
                contact=contact,
                phone=phone,
                is_primary=is_primary
            ).clean()
        except DjangoValidationError as err:
            raise ValidationError(detail=as_serializer_error(err))


class GroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = Group
        fields = (
            'id',
            'name',
            'description',
            'created_by',
            'created_at',
            'updated_by',
            'updated_at',
        )
        read_only_fields = fields


class GroupDeserializer(serializers.ModelSerializer):

    class Meta:
        model = Group
        fields = (
            'name',
            'description',
        )

    @transaction.atomic
    def save(self, **kwargs) -> Group:
        """
        We override this method to set the (`Group.created_by`, `Group.updated_by`) fields
        accordingly and add the group's creator as the group admin.
        """
        contact = self.context['request'].user.contact

        # If update
        if self.instance:
            instance = super().save(updated_by=contact)
        # If create
        else:
            instance = super().save(created_by=contact)

        # Add group's creator as an admin on that group
        instance.contacts.add(
            contact,
            through_defaults={'role': ContactGroup.ROLE_ADMIN, 'inviter': contact}
        )

        return instance


class ContactGroupSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    email = serializers.EmailField(source='user.email')
    phone_numbers = serializers.SerializerMethodField()
    # Assuming the `serializer.instance` comes with preselected `role` field
    role = serializers.CharField()
    # Assuming the `serializer.instance` comes with preselected `invited_by` field
    invited_by = serializers.IntegerField()
    # Assuming the `serializer.instance` comes with preselected `joined_at` field
    joined_at = serializers.DateTimeField()

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
            'role',
            'invited_by',
            'joined_at',
        )
        read_only_fields = fields

    def get_phone_numbers(self, obj) -> List[Dict]:
        # Assuming that `obj` comes with
        # prefetched `phone_numbers` attribute
        return [
            {
                'id': p.id,
                'phone_number': {
                    'value': p.phone_number.national_number,
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


class ContactGroupDeserializer(serializers.Serializer):
    contact = serializers.PrimaryKeyRelatedField(
        queryset=Contact.objects.all()
    )
    role = serializers.ChoiceField(
        choices=ContactGroup.ROLE_CHOICES
    )
    inviter = serializers.PrimaryKeyRelatedField(
        queryset=Contact.objects.all()
    )

    class Meta:
        fields = (
            'contact',
            'role',
            'inviter',
        )

    @transaction.atomic
    def create(self, validated_data) -> Contact:
        contact = validated_data.get('contact')
        role = validated_data.get('role')
        inviter = validated_data.get('inviter')

        # Assuming the serializer's context comes with the `group` object
        group = self.context.get('group')
        group.contacts.add(contact, through_defaults={'role': role, 'inviter': inviter})

        return contact

    def update(self, instance, validated_data):
        # Preventive action (`contact`, `inviter`) fields
        # should never be modified on update
        role = validated_data.get('role')

        # Assuming the serializer's context comes with the `group` object
        group = self.context.get('group')
        ContactGroup.objects.filter(contact=instance, group=group).update(role=role)

        return instance
