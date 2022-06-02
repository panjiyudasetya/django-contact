from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


User = get_user_model()


class Phone(models.Model):
    phone_number = PhoneNumberField()

    TYPE_CELLPHONE = "cellphone"
    TYPE_TELEPHONE = "telephone"
    TYPE_TELEFAX = "telefax"
    PHONE_TYPE_CHOICES = (
        (TYPE_CELLPHONE, 'Cellular phone'),
        (TYPE_TELEPHONE, 'Telephone'),
        (TYPE_TELEFAX, 'Facsimile'),
    )
    phone_type = models.CharField(
        max_length=9,
        choices=PHONE_TYPE_CHOICES
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (
            ('phone_number', 'phone_type'),
        )


class Contact(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )
    nickname = models.CharField(
        max_length=128,
        blank=True
    )
    company = models.CharField(
        max_length=128,
        blank=True
    )
    title = models.CharField(
        max_length=128,
        blank=True
    )
    phone_numbers = models.ManyToManyField(
        Phone,
        through='ContactPhone',
        through_fields=('contact', 'phone')
    )
    address = models.CharField(
        max_length=256,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    contacts = models.ManyToManyField(
        'self',
        through='ContactMembership',
        through_fields=('owner', 'contact')
    )


class ContactMembership(models.Model):
    owner = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name='contact_of'
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE
    )
    starred = models.BooleanField(default=False)


class ContactPhone(models.Model):
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE
    )
    phone = models.ForeignKey(
        Phone,
        on_delete=models.CASCADE
    )
    is_primary = models.BooleanField(default=False)

    class Meta:
        unique_together = (
            ('contact', 'phone'),
        )

    def clean(self) -> None:
        if self.is_primary and self._has_primary_phone():
            raise ValidationError(
                'Contact ID {} has primary phone already.'.format(self.contact_id)
            )

    def _has_primary_phone(self):
        """
        Return `True` if the `self.contact` has primary phone already.
        """
        return ContactPhone.objects.filter(
            contact_id=self.contact_id,
            is_primary=True
        ).exists()


class Group(models.Model):
    name = models.CharField(
        max_length=128,
        unique=True
    )
    description = models.CharField(
        max_length=256,
        blank=True
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL,
        related_name='groups_as_updater'
    )
    updated_at = models.DateTimeField(auto_now=True)
    contacts = models.ManyToManyField(
        Contact,
        through='ContactGroup',
        through_fields=('group', 'contact'),
    )

    def is_group_admin(self, contact) -> bool:
        """
        Return `True` if the given `contact` is the admin
        of the Group instance.
        """
        return ContactGroup.objects.filter(
            group=self,
            contact=contact,
            role=self.ROLE_ADMIN
        ).exists()

    def is_group_member(self, contact) -> bool:
        """
        Return `True` if the given `contact` is a member
        of the Group instance.
        """
        return ContactGroup.objects.filter(
            group=self,
            contact=contact
        ).exists()


class ContactGroup(models.Model):
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE
    )

    ROLE_ADMIN = 'admin'
    ROLE_MEMBER = 'member'
    ROLE_CHOICES = (
        (ROLE_ADMIN, 'Admin'),
        (ROLE_MEMBER, 'Member'),
    )
    role = models.CharField(
        max_length=6,
        choices=ROLE_CHOICES,
        default=ROLE_MEMBER
    )

    inviter = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name='contactgroups_as_inviter'
    )
    joined_at = models.DateTimeField(auto_now_add=True)
