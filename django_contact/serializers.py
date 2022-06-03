from rest_framework import serializers

from .models import Contact

class ContactSerializer(serializers.ModelSerializer):
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
        return [
            {
                'phone_number': phone.phone_number,
                'type': phone.phone_type,
                'created_at': phone.created_at,
                'updated_at': phone.updated_at
            }
            for phone in obj.phone_numbers.all()
        ]
    
    def get_starred(self, obj):
        # Assumes that `obj` comes with
        # the `starred` annotated attribute
        return obj.starred
