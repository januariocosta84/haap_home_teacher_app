from types import SimpleNamespace

from django.template.loader import render_to_string
from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from core.models import User
from preschools.models import Preschool
from ticket.models import SupportTicket


class SupportTicketModelTests(TestCase):
    def test_ticket_string_representation_uses_ticket_number_only(self):
        teacher = User.objects.create_user(
            username='teacher1',
            whatsapp_number='123456789',
            role='teacher',
            first_name='Emanuel',
            last_name='Moniz',
        )
        preschool = Preschool.objects.create(
            name='Test Preschool',
            preschool_type='government',
        )

        ticket = SupportTicket.objects.create(
            ticket_number='TKT-TEST01',
            teacher=teacher,
            preschool=preschool,
        )

        self.assertEqual(str(ticket), 'TKT-TEST01')


class SupportTicketTemplateTests(SimpleTestCase):
    def test_ticket_detail_template_renders_ticket_messages_from_ticket_messages_context(self):
        class DummyTicket:
            ticket_number = 'TKT-TEST02'
            created_at = timezone.now()
            status = 'open'
            priority = 'medium'
            resolution_note = ''
            pk = 'ticket-123'
            is_equipment_request = True
            is_training_request = False

            def get_status_display(self):
                return 'Open'

            def get_priority_display(self):
                return 'Medium'

        ticket = DummyTicket()
        ticket.teacher = SimpleNamespace(first_name='Emanuel', last_name='Moniz')
        ticket.preschool = SimpleNamespace(name='Test Preschool')
        ticket.classroom = None

        ticket_message = SimpleNamespace(
            sender_label='Teacher',
            sender=SimpleNamespace(first_name='Emanuel', last_name='Moniz'),
            created_at=timezone.now(),
            message='This is a ticket reply.',
            is_admin_reply=False,
        )

        rendered = render_to_string(
            'ticket/support_ticket_detail.html',
            {
                'ticket': ticket,
                'problem_items': [],
                'details': [],
                'items': [],
                'ticket_messages': [ticket_message],
                'reply_form': None,
                'user': SimpleNamespace(role='teacher'),
            },
        )

        self.assertIn('This is a ticket reply.', rendered)
        self.assertNotIn('Seidauk iha resposta.', rendered)
