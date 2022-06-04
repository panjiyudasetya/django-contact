from rest_framework import serializers

from .models import Contact


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

    def get_phone_numbers(self, obj):
        # Assuming that `obj` comes with
        # prefetched `phone_numbers` attribute
        return [
            {
                'phone_number': phone.phone_number,
                'type': phone.phone_type,
                'is_primary': phone.is_primary,
                'created_at': phone.created_at,
                'updated_at': phone.updated_at
            }
            for phone in obj._prefetched_objects_cache['phone_numbers']
        ]


class ContactDetailSerializer(serializers.ModelSerializer):
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

    def get_phone_numbers(self, obj):
        # Assuming that `obj` comes with
        # prefetched `phone_numbers` attribute
        return [
            {
                'phone_number': phone.phone_number,
                'type': phone.phone_type,
                'is_primary': phone.is_primary,
                'created_at': phone.created_at,
                'updated_at': phone.updated_at
            }
            for phone in obj._prefetched_objects_cache['phone_numbers']
        ]

    def get_starred(self, obj):
        # Assuming that `obj` comes with
        # preselected `starred` attribute
        return obj.starred
