# ticket/models.py
import uuid
from django.db import models
from core.models import User
from preschools.models import Preschool
from klase.models import Classroom
import random
import string


def generate_ticket_number():
    """Generate unique ticket number"""
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"TKT-{suffix}"


class SupportTicket(models.Model):

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed'),
        ('resolved', 'Resolved'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    ticket_number = models.CharField(
        max_length=30,
        unique=True,
        default=generate_ticket_number
    )

    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='support_tickets',
        limit_choices_to={'role': 'teacher'}
    )

    preschool = models.ForeignKey(
        Preschool,
        on_delete=models.CASCADE,
        related_name='support_tickets'
    )

    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='support_tickets'
    )

    # Main categorization
    is_equipment_request = models.BooleanField(default=True)
    is_training_request = models.BooleanField(default=False)

    # General details
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open'
    )

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium'
    )

    resolution_note = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'support_tickets'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.ticket_number} - {self.teacher}"


class SupportTicketItem(models.Model):
    """Individual support request items within a ticket"""

    EQUIPMENT_ITEM_CHOICES = [
        ('projector_lamp', '1. Troka lâmpada projetor'),
        ('miracast_config', '2. Ajuda atu halo konfigurasaun Miracast (tablet Android ba projetor Epson)'),
        ('projector_support', '3. Suporta projetor – hadia ka troka'),
        ('screen_problem', '4. Tela klen – problema'),
        ('tablet_technical', '5. Tablet – problema tékniku'),
        ('tablet_lost', '6. Tablet – na\'ok'),
        ('tablet_damaged', '7. Tablet – estragu'),
        ('projector_damaged', '8. Projetor – estragu ka la funsiona la\'ós ho lâmpada'),
        ('cable_adapter', '9. Problema ho kabelu ka adaptador (HDMI, USB-C, etc.)'),
        ('other_equipment', '10. Problema seluk ho ekipamentu AV iha sala aula'),
    ]

    TRAINING_ITEM_CHOICES = [
        ('general_training', '11. Husu formasaun jerál ba mestri kona-ba uza aplikasaun ne\'e ba ensinu'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.CASCADE,
        related_name='items'
    )

    # Type of item
    item_type = models.CharField(
        max_length=50,
        choices=EQUIPMENT_ITEM_CHOICES + TRAINING_ITEM_CHOICES
    )

    # Details provided by user
    details = models.TextField(blank=True, null=True)

    # Additional field for training requests
    preferred_format = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Preferred training format (ex.: hadau hadap malu, vídeo guia, workshop ho grupu, 1:1)"
    )

    app_features_to_learn = models.TextField(
        blank=True,
        null=True,
        help_text="Application features to learn (ex.: navigasaun, konfigurasaun, jestaun klase)"
    )

    class Meta:
        db_table = 'support_ticket_items'

    def __str__(self):
        return f"{self.ticket.ticket_number} - {self.item_type}"


class SupportCategory(models.Model):

    title = models.CharField(max_length=255)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'support_categories'

    def __str__(self):
        return self.title