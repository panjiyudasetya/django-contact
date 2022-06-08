from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from typing import Dict, List

from django_contact.models import (
    Contact,
    Phone,
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
        # When that `obj` comes with prefetched `phone_numbers`, use it.
        if hasattr(obj, '_prefetched_objects_cache'):
            phone_numbers = obj._prefetched_objects_cache.get('phone_numbers', [])

        # Otherwise, select it from DB.
        # Please be carefull with this, it can cause the endpoint performance
        # extremely slow, because each object will execute 1 DB lookup query.
        else:
            phone_numbers = obj.phone_numbers.all()

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
            for p in phone_numbers
        ]


class ContactDeserializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False
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

    def validate_user(self, value) -> User:
        if Contact.objects.filter(user=value).exists():
            raise ValidationError(
                'Contact for User ID {} is already exists.'.format(value.id),
                code='invalid'
            )
        return value

    def validate(self, attrs) -> Dict:
        # Checks on create
        if not self.instance and not attrs.get('user'):
            raise ValidationError(
                {'user': 'This field is required'},
                code='required'
            )
        return super().validate(attrs)

    def update(self, instance, validated_data) -> Contact:
        # The `user` field should never be modified on update
        # Therefore, we need to remove it from the `validated_data` object
        validated_data.pop('user', None)
        return super().update(instance, validated_data)


class SerializerContactDefault:
    requires_context = True

    def __call__(self, serializer_field) -> Contact:
        return serializer_field.context['contact']

    def __repr__(self) -> str:
        return '%s()' % self.__class__.__name__


class PhoneSerializer(serializers.ModelSerializer):
    phone_number = serializers.SerializerMethodField()
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
    contact = serializers.HiddenField(
        default=SerializerContactDefault()
    )
    is_primary = serializers.BooleanField(required=False)

    class Meta:
        model = Phone
        fields = (
            'contact',
            'phone_number',
            'phone_type',
            'is_primary',
        )

    def update(self, instance, validated_data) -> Phone:
        # The `contact` attribute should never be modified
        validated_data.pop('contact', None)
        return super().update(instance, validated_data)


class MyContactSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    email = serializers.EmailField(source='user.email')
    phone_numbers = serializers.SerializerMethodField()
    # Assuming the `serializer.instance` comes with preselected `starred` field
    starred = serializers.BooleanField(default=False)

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
            'starred',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields

    def get_phone_numbers(self, obj) -> List[Dict]:
        # When that `obj` comes with prefetched `phone_numbers`, use it.
        if hasattr(obj, '_prefetched_objects_cache'):
            phone_numbers = obj._prefetched_objects_cache.get('phone_numbers', [])

        # Otherwise, select it from DB.
        # Please be carefull with this, it can cause the endpoint performance
        # extremely slow, because each object will execute 1 DB lookup query.
        else:
            phone_numbers = obj.phone_numbers.all()

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
            for p in phone_numbers
        ]


class MyContactDeserializer(serializers.Serializer):
    contact = serializers.PrimaryKeyRelatedField(
        queryset=Contact.objects.all()
    )
    starred = serializers.BooleanField(default=False)

    class Meta:
        fields = ('contact', 'starred',)

    def validate(self, attrs) -> Dict:
        # On create's validations
        if not self.instance:
            contact = attrs['contact']

            # Assuming the serializer's context comes with the `contact` object
            user_contact = self.context['request'].user.contact
            if user_contact.contacts.all().filter(id=contact.id).exists():
                raise ValidationError(
                    {'contact': 'Contact ID {} is already exists.'.format(contact.id)}
                )

        return super().validate(attrs)

    @transaction.atomic
    def create(self, validated_data) -> Contact:
        contact = validated_data.get('contact')
        starred = validated_data.get('starred')

        # Assuming the serializer's context comes with the `contact` object
        user_contact = self.context['request'].user.contact
        user_contact.contacts.add(contact, through_defaults={'starred': starred})

        # `Contact` successfully added to the `user_contact` list,
        # Setting the `starred` attribute so that it can be serialized in the API response
        setattr(contact, 'starred', starred)
        return contact


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
    def create(self, validated_data):
        """
        We override this method to set the `Group.created_by`
        and add the group's creator as the group admin.
        """
        contact = self.context['request'].user.contact
        validated_data['created_by'] = contact

        # Add group's creator as an admin of that group
        instance = super().create(validated_data)
        instance.contacts.add(
            contact,
            through_defaults={'role': ContactGroup.ROLE_ADMIN, 'inviter': contact}
        )
        return instance

    def update(self, instance, validated_data):
        """
        We override this method to set the `Group.updated_by`.
        """
        validated_data['updated_by'] = self.context['request'].user.contact
        return super().update(instance, validated_data)


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
        # When that `obj` comes with prefetched `phone_numbers`, use it.
        if hasattr(obj, '_prefetched_objects_cache'):
            phone_numbers = obj._prefetched_objects_cache.get('phone_numbers', [])

        # Otherwise, select it from DB.
        # Please be carefull with this, it can cause the endpoint performance
        # extremely slow, because each object will execute 1 DB lookup query.
        else:
            phone_numbers = obj.phone_numbers.all()

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
            for p in phone_numbers
        ]


class SerializerGroupDefault:
    requires_context = True

    def __call__(self, serializer_field) -> Contact:
        return serializer_field.context['group']

    def __repr__(self) -> str:
        return '%s()' % self.__class__.__name__


class ContactGroupCreateDeserializer(serializers.Serializer):
    group = serializers.HiddenField(default=SerializerGroupDefault())
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
            'group',
            'role',
            'inviter',
        )

    def create(self, validated_data):
        contact = validated_data.get('contact')

        # Assuming the serializer's context comes with the `group` object
        group = self.context.get('group')
        group.contacts.add(
            contact,
            through_defaults={
                'role': validated_data.get('role'),
                'inviter': validated_data.get('inviter')
            }
        )

        # Return that newly added contact with prefetched additional data.
        return group.get_members().get(id=contact.id)


class ContactGroupUpdateDeserializer(serializers.Serializer):
    role = serializers.ChoiceField(
        choices=ContactGroup.ROLE_CHOICES
    )

    class Meta:
        fields = ('role',)

    def update(self, instance, validated_data):
        # Assuming the serializer's context comes with the `group` object
        group = self.context.get('group')
        group.contactgroup_set.filter(contact=instance).update(**validated_data)

        # Return that newly updated contact with prefetched additional data.
        return group.get_members().get(id=instance.id)
