import uuid
from django.db import models
from preschools.models import Preschool
from klase.models import Classroom
from core.models import User
from django.conf import settings
from core.models import User
from preschools.models import Preschool



class Equipment(models.Model):

    TYPE_CHOICES = [
        ('tablet', 'Tablet'),
        ('projector', 'Projector'),
        ('screen', 'Screen'),
        ('adapter', 'Adapter'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    equipment_type = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES
    )

    model_number = models.CharField(max_length=100)

    serial_number = models.CharField(
        max_length=100,
        unique=True
    )

    preschool = models.ForeignKey(
        Preschool,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    teacher = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'equipments'

class EquipmentHistory(models.Model):
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name='history'
    )

    old_preschool = models.ForeignKey(
        Preschool,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='old_equipment_history'
    )

    new_preschool = models.ForeignKey(
        Preschool,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='new_equipment_history'
    )

    changed_at = models.DateTimeField(auto_now_add=True)


class AssetMovement(models.Model):

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('returned', 'Returned'),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='asset_movements'
    )

    preschool = models.ForeignKey(
        Preschool,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    registered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='registered_assets'
    )

    registration_date = models.DateField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    note = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'asset_movements'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.teacher} - {self.registration_date}"


class AssetMovementItem(models.Model):

    CONDITION_CHOICES = [
        ('new', 'Foun'),
        ('good', 'Diak'),
        ('damaged', 'Aat'),
        ('repair', 'Presiza Hadia'),
    ]

    movement = models.ForeignKey(
        AssetMovement,
        on_delete=models.CASCADE,
        related_name='items'
    )

    equipment = models.ForeignKey(
        'Equipment',
        on_delete=models.CASCADE
    )

    serial_number = models.CharField(max_length=100)

    condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES
    )

    class Meta:
        db_table = 'asset_movement_items'

    def __str__(self):
        return self.serial_number
