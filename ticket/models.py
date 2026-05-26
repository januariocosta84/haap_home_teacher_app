# Create your models here.
import uuid
from django.db import models
from core.models import User
from preschools.models import Preschool


class SupportTicket(models.Model):

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    ticket_number = models.CharField(
        max_length=30,
        unique=True
    )

    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='support_tickets'
    )

    preschool = models.ForeignKey(
        Preschool,
        on_delete=models.CASCADE
    )

    details = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open'
    )

    resolution_note = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'support_tickets'


class SupportCategory(models.Model):

    title = models.CharField(max_length=255)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'support_categories'