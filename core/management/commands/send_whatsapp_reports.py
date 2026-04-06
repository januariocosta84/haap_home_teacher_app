"""
Django management command to generate and send child activity reports via WhatsApp
Usage: python manage.py send_whatsapp_reports [--days 30] [--parent-id UUID]
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from core.services.report_generator import get_report_generator
from core.services.whatsapp_service import get_whatsapp_service
from core.models import Child
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Generate child activity reports and send via WhatsApp to parents'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to include in report (default: 30)'
        )
        parser.add_argument(
            '--parent-id',
            type=str,
            help='Send report only to specific parent (UUID)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show reports without sending them'
        )
        parser.add_argument(
            '--child-id',
            type=str,
            help='Send report for specific child only (UUID)'
        )
    
    def handle(self, *args, **options):
        days = options.get('days', 30)
        parent_id = options.get('parent_id')
        dry_run = options.get('dry_run', False)
        child_id = options.get('child_id')
        
        self.stdout.write(
            self.style.SUCCESS(f'🚀 Starting WhatsApp report generation (last {days} days)...')
        )
        
        # Initialize services
        report_generator = get_report_generator(days=days)
        whatsapp_service = get_whatsapp_service()
        
        # Check if WhatsApp is configured
        if not whatsapp_service.enabled:
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  WhatsApp service is not configured. '
                    'Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_WHATSAPP_FROM in .env'
                )
            )
            if not dry_run:
                raise CommandError('WhatsApp configuration missing')
        
        # Get parents to send reports to
        parents = self._get_parents(parent_id)
        if not parents:
            self.stdout.write(
                self.style.WARNING('No parents found to send reports to')
            )
            return
        
        sent_count = 0
        failed_count = 0
        
        for parent in parents:
            # Get children for this parent
            if child_id:
                children = Child.objects.filter(parent=parent, id=child_id)
            else:
                children = Child.objects.filter(parent=parent)
            
            if not children.exists():
                self.stdout.write(
                    self.style.WARNING(f'No children found for parent {parent.get_full_name()}')
                )
                continue
            
            for child in children:
                try:
                    # Generate report
                    report = report_generator.generate_child_report(child)
                    message = report_generator.format_whatsapp_message(report)
                    
                    self.stdout.write(
                        self.style.HTTP_INFO(
                            f'\n📄 Report for {child.first_name} (Parent: {parent.get_full_name()})'
                        )
                    )
                    self.stdout.write(f'Phone: {parent.whatsapp_number}')
                    self.stdout.write('---')
                    self.stdout.write(message)
                    self.stdout.write('---\n')
                    
                    # Send report
                    if not dry_run:
                        if whatsapp_service.send_message(parent.whatsapp_number, message):
                            self.stdout.write(
                                self.style.SUCCESS(f'✅ Report sent to {parent.get_full_name()}')
                            )
                            sent_count += 1
                        else:
                            self.stdout.write(
                                self.style.ERROR(
                                    f'❌ Failed to send report to {parent.get_full_name()}'
                                )
                            )
                            failed_count += 1
                    else:
                        self.stdout.write(
                            self.style.SUCCESS('[DRY RUN] Report would be sent')
                        )
                        sent_count += 1
                
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'Error generating report for {child.first_name}: {str(e)}'
                        )
                    )
                    failed_count += 1
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'✅ Reports sent: {sent_count}'))
        if failed_count > 0:
            self.stdout.write(self.style.ERROR(f'❌ Reports failed: {failed_count}'))
        self.stdout.write('='*50)
    
    def _get_parents(self, parent_id: str = None) -> list:
        """Get parents to send reports to"""
        if parent_id:
            try:
                parent = User.objects.get(id=parent_id, role='parent')
                return [parent]
            except User.DoesNotExist:
                raise CommandError(f'Parent with ID {parent_id} not found')
        else:
            # Get all parents with children
            return list(
                User.objects.filter(role='parent', children__isnull=False).distinct()
            )
