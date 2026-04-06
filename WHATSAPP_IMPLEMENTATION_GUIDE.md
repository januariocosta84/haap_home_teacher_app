"""
Integration guide for WhatsApp Report System

This file provides quick integration steps for adding the WhatsApp report
functionality to your existing Django application.
"""

# ============================================================================
# STEP 1: Add API Endpoints to urls.py
# ============================================================================
# Add this to your core/urls.py:

"""
from django.urls import path
from core.api_reports import send_child_report_api, send_all_reports_api

urlpatterns = [
    # ... existing patterns ...
    
    # WhatsApp Report API endpoints
    path('api/send-child-report/<uuid:child_id>/', send_child_report_api, name='send_child_report_api'),
    path('api/send-all-reports/', send_all_reports_api, name='send_all_reports_api'),
]
"""


# ============================================================================
# STEP 2: Add to requirements.txt
# ============================================================================
# Add this to requirements.txt:
"""
twilio==9.2.0
"""

# Then run:
# pip install -r requirements.txt


# ============================================================================
# STEP 3: Configure .env file
# ============================================================================
# Add these variables to .env:
"""
# Twilio WhatsApp Configuration
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_FROM=whatsapp:+1234567890
"""


# ============================================================================
# STEP 4: Usage Examples
# ============================================================================

# Example 1: Generate and send report from view
# ============================================================================
from core.services.report_generator import get_report_generator
from core.services.whatsapp_service import get_whatsapp_service
from core.models import Child
from django.http import JsonResponse

def send_report_view(request, child_id):
    """Example view to send a report for a child"""
    try:
        child = Child.objects.get(id=child_id)
        
        # Check permissions
        if request.user.role == 'parent' and child.parent != request.user:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        # Generate report
        generator = get_report_generator(days=30)
        report = generator.generate_child_report(child)
        message = generator.format_whatsapp_message(report)
        
        # Send via WhatsApp
        whatsapp = get_whatsapp_service()
        success = whatsapp.send_message(child.parent.whatsapp_number, message)
        
        return JsonResponse({
            'success': success,
            'message': 'Report sent' if success else 'Failed to send',
            'report': report
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# Example 2: Send bulk reports
# ============================================================================
def send_all_reports_view(request):
    """Send reports to all parents"""
    if request.user.role not in ['parent', 'moe_admin']:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    parentsto_send = [request.user] if request.user.role == 'parent' else \
                     list(User.objects.filter(role='parent', children__isnull=False).distinct())
    
    generator = get_report_generator(days=30)
    whatsapp = get_whatsapp_service()
    
    results = {'sent': 0, 'failed': 0}
    
    for parent in parentsto_send:
        for child in parent.children.all():
            try:
                report = generator.generate_child_report(child)
                message = generator.format_whatsapp_message(report)
                if whatsapp.send_message(parent.whatsapp_number, message):
                    results['sent'] += 1
                else:
                    results['failed'] += 1
            except Exception as e:
                results['failed'] += 1
    
    return JsonResponse(results)


# Example 3: Custom report format
# ============================================================================
from core.services.report_generator import ChildReportGenerator

class CustomReportGenerator(ChildReportGenerator):
    """Extend the default generator with custom formatting"""
    
    def format_whatsapp_message(self, report):
        """Custom message format"""
        return f"""
Hello {report['parent_name']},

Progress report for {report['child_name']}:
- Total activities: {report['total_activities']}
- Achievements: {report['achieved_activities']} ({report['achievement_rate']}%)

Period: Last {report['period_days']} days

Best regards,
HAAP System
"""


# Example 4: Periodic task with Celery
# ============================================================================
# If using Celery, add to core/tasks.py:

from celery import shared_task
from core.services.report_generator import get_report_generator
from core.services.whatsapp_service import get_whatsapp_service
from core.models import Child, User

@shared_task
def send_monthly_reports(days=30):
    """Send activity reports to all parents"""
    generator = get_report_generator(days=days)
    whatsapp = get_whatsapp_service()
    
    parents = User.objects.filter(role='parent', children__isnull=False).distinct()
    results = {'sent': 0, 'failed': 0}
    
    for parent in parents:
        for child in parent.children.all():
            try:
                report = generator.generate_child_report(child)
                message = generator.format_whatsapp_message(report)
                if whatsapp.send_message(parent.whatsapp_number, message):
                    results['sent'] += 1
                else:
                    results['failed'] += 1
            except Exception as e:
                results['failed'] += 1
    
    return results

# Schedule it in your Celery beat schedule:
# CELERY_BEAT_SCHEDULE = {
#     'send-monthly-reports': {
#         'task': 'core.tasks.send_monthly_reports',
#         'schedule': crontab(day_of_month='1', hour=8, minute=0),  # 1st of month at 8am
#     },
# }


# Example 5: Django signal to send report when activity is logged
# ============================================================================
# Add to core/signals.py:

from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import ActivityResult
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=ActivityResult)
def send_report_on_milestone(sender, instance, created, **kwargs):
    """Send weekly report when parent logs activities"""
    if not created:
        return
    
    from datetime import datetime, timedelta
    from core.services.report_generator import get_report_generator
    from core.services.whatsapp_service import get_whatsapp_service
    
    # Check if it's time for weekly report (e.g., every Monday)
    if datetime.now().weekday() != 0:  # Only on Mondays
        return
    
    try:
        child = instance.student
        parent = instance.parent
        
        if not parent or not child:
            return
        
        # Generate weekly report
        generator = get_report_generator(days=7)
        report = generator.generate_child_report(child)
        message = generator.format_whatsapp_message(report)
        
        # Send
        whatsapp = get_whatsapp_service()
        whatsapp.send_message(parent.whatsapp_number, message)
    
    except Exception as e:
        logger.error(f'Error sending automatic report: {str(e)}')

# Register in apps.py:
# from django.apps import AppConfig
# class CoreConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'core'
#     
#     def ready(self):
#         import core.signals  # Import signals when app is ready


# ============================================================================
# TESTING THE SYSTEM
# ============================================================================

# Test in Django shell:
"""
python manage.py shell

from core.services.report_generator import get_report_generator
from core.services.whatsapp_service import get_whatsapp_service
from core.models import Child

# Get a child
child = Child.objects.first()

# Generate report
generator = get_report_generator(days=30)
report = generator.generate_child_report(child)
message = generator.format_whatsapp_message(report)
print(message)

# Send (if configured)
whatsapp = get_whatsapp_service()
print(f'Service enabled: {whatsapp.enabled}')
if whatsapp.enabled:
    success = whatsapp.send_message(child.parent.whatsapp_number, message)
    print(f'Sent: {success}')
"""

# Run management command:
# python manage.py send_whatsapp_reports --dry-run
# python manage.py send_whatsapp_reports --child-id <uuid>
# python manage.py send_whatsapp_reports --days 7
