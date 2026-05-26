from django.db import models
from django.db import models
from core.models import Municipality, AdministrativePost, Suco, Aldeia, User
import uuid

class Preschool(models.Model):

    TYPE_CHOICES = [
        ('government', 'Government'),
        ('community', 'Community'),
        ('private', 'Private'),
        ('playgroup', 'Playgroup'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=255)

    municipality = models.ForeignKey(
        Municipality,
        on_delete=models.SET_NULL,
        null=True
    )

    administrative_post = models.ForeignKey(
        AdministrativePost,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    suco = models.ForeignKey(
        Suco,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    aldeia = models.ForeignKey(
        Aldeia,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    preschool_type = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES
    )

    whatsapp_contact = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    email = models.EmailField(blank=True, null=True)

    # GEOLOCATION
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_preschools'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'preschools'
        ordering = ['name']

    def __str__(self):
        return self.name


class PreschoolTeacher(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    preschool = models.ForeignKey(
        Preschool,
        on_delete=models.CASCADE,
        related_name='teachers'
    )

    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assigned_preschools',
        limit_choices_to={'role': 'teacher'}
    )

    is_primary = models.BooleanField(default=False)   # main school
    assigned_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False)  # for admin approval

    class Meta:
        db_table = "preschool_teachers"
        unique_together = ('preschool', 'teacher')

    def __str__(self):
        return f"{self.teacher.get_full_name()} -> {self.preschool.name}"