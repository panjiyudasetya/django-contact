from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, F, Prefetch
from phonenumber_field.modelfields import PhoneNumberField


User = get_user_model()


class PhoneQuerySet(models.QuerySet):

    def annotate_is_primary(self) -> models.QuerySet['Phone']:
        """
        This method annotates the `self` queryset with the `is_primary` attribute
        taken from the `ContactPhone`.
        """
        return self.annotate(is_primary=F('contactphone__is_primary'))


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

    objects = PhoneQuerySet.as_manager()

    class Meta:
        unique_together = (
            ('phone_number', 'phone_type'),
        )


class ContactQuerySet(models.QuerySet):

    def prefetch_phone_numbers(self) -> models.QuerySet['Contact']:
        """
        This method prefetches the `self` queryset with `phone_numbers` attribute.
        """
        prefetch_phone_numbers = Prefetch(
            'phone_numbers',
            Phone.objects.all().annotate(is_primary=F('contactphone__is_primary'))
        )
        return self.prefetch_related(prefetch_phone_numbers)

    def annotate_starred(self) -> models.QuerySet['Contact']:
        """
        This method annotates the `self` queryset with the `starred` attribute
        taken from the `ContactMembership`.
        """
        return self.annotate(starred=F('contactmembership__starred'))


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

    objects = ContactQuerySet.as_manager()


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

    def _has_primary_phone(self) -> bool:
        """
        Return `True` if the `self.contact` has primary phone already.
        """
        return ContactPhone.objects.filter(
            contact_id=self.contact_id,
            is_primary=True
        ).exists()


class GroupQuerySet(models.QuerySet):

    def accessible_for(self, contact) -> models.QuerySet['Group']:
        """
        This method narrows down the `self` queryset to the union of:
        - Groups created by the contact.
        - Groups where the contact is a member of.
        """
        return self.filter(
            Q(created_by=contact) | Q(contactgroup__contact=contact)
        ).distinct()


class Group(models.Model):
    name = models.CharField(max_length=128)
    description = models.CharField(
        max_length=256,
        blank=True
    )
    created_by = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name='groups_as_creator'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        Contact,
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

    objects = GroupQuerySet.as_manager()

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

    def get_contacts(self) -> models.QuerySet['Contact']:
        """
        Returns `Contact` instances that are currenlty member of the `self` instance
        with annotated (`role`, `inviter`, `joined_at`).

        Those annotated attributes are taken from the `ContactGroup`.
        """

        return self.contacts.all().prefetch_phone_numbers()\
            .annotate(role=F('contactgroup__role'))\
            .annotate(invited_by=F('contactgroup__inviter'))\
            .annotate(joined_at=F('contactgroup__joined_at'))\
            .order_by('id').distinct()


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

    class Meta:
        unique_together = (
            ('contact', 'group'),
        )
