from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import User
from .models import Notification, SupportTicket, SupportTicketMessage


@receiver(post_save, sender=SupportTicket)
def notify_admins_new_ticket(sender, instance, created, **kwargs):
    if not created:
        return
    admins = User.objects.filter(role='moe_admin', is_active=True)
    teacher_name = instance.teacher.get_full_name() or instance.teacher.username
    Notification.objects.bulk_create([
        Notification(
            recipient=admin,
            ticket=instance,
            notification_type='new_ticket',
            title=f'Tiket Foun: {instance.ticket_number}',
            message=f'Mestri {teacher_name} husi {instance.preschool.name} submete tiket suporta foun.',
        )
        for admin in admins
    ])


@receiver(post_save, sender=SupportTicketMessage)
def notify_teacher_admin_reply(sender, instance, created, **kwargs):
    if not created or instance.sender_type != 'admin':
        return
    admin_name = instance.sender.get_full_name() or instance.sender.username
    Notification.objects.create(
        recipient=instance.ticket.teacher,
        ticket=instance.ticket,
        notification_type='new_reply',
        title=f'Resposta Foun: {instance.ticket.ticket_number}',
        message=f'Admin {admin_name} hatama resposta foun ba ita nia tiket.',
    )
