"""
API views for sending WhatsApp reports
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from core.models import Child, User
from core.services.report_generator import get_report_generator
from core.services.whatsapp_service import get_whatsapp_service
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_child_report_api(request, child_id):
    """
    Send WhatsApp report for a specific child
    
    POST /api/send-child-report/{child_id}/
    
    Response: {
        'success': bool,
        'message': str,
        'report': dict
    }
    """
    try:
        child = get_object_or_404(Child, id=child_id)
        
        # Check permissions: parent can only send for their own children
        if request.user.role == 'parent' and child.parent != request.user:
            return Response(
                {'error': 'You do not have permission to send reports for this child'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Generate report
        days = request.data.get('days', 30)
        report_generator = get_report_generator(days=days)
        report = report_generator.generate_child_report(child)
        message = report_generator.format_whatsapp_message(report)
        
        # Send via WhatsApp
        whatsapp_service = get_whatsapp_service()
        parent = child.parent
        
        if not whatsapp_service.enabled:
            return Response(
                {
                    'success': False,
                    'error': 'WhatsApp service not configured',
                    'report': report
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        success = whatsapp_service.send_message(parent.whatsapp_number, message)
        
        return Response({
            'success': success,
            'message': 'Report sent successfully' if success else 'Failed to send report',
            'report': report,
            'recipient': parent.whatsapp_number
        })
    
    except Exception as e:
        logger.error(f'Error sending report: {str(e)}')
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_all_reports_api(request):
    """
    Send WhatsApp reports for all children of authenticated parent
    or all parents (if MOE admin)
    
    POST /api/send-all-reports/
    
    Response: {
        'success': int,
        'failed': int,
        'message': str
    }
    """
    try:
        days = request.data.get('days', 30)
        
        # Determine which parents to send reports for
        if request.user.role == 'parent':
            parents = [request.user]
        elif request.user.role == 'moe_admin':
            parents = list(User.objects.filter(role='parent', children__isnull=False).distinct())
        else:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Initialize services
        report_generator = get_report_generator(days=days)
        whatsapp_service = get_whatsapp_service()
        
        if not whatsapp_service.enabled:
            return Response(
                {
                    'success': False,
                    'error': 'WhatsApp service not configured'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        results = {'sent': 0, 'failed': 0}
        
        for parent in parents:
            children = Child.objects.filter(parent=parent)
            for child in children:
                try:
                    report = report_generator.generate_child_report(child)
                    message = report_generator.format_whatsapp_message(report)
                    
                    if whatsapp_service.send_message(parent.whatsapp_number, message):
                        results['sent'] += 1
                    else:
                        results['failed'] += 1
                except Exception as e:
                    logger.error(f'Error sending report for child {child.id}: {str(e)}')
                    results['failed'] += 1
        
        return Response({
            'success': results['sent'],
            'failed': results['failed'],
            'message': f"Sent {results['sent']} reports, failed: {results['failed']}"
        })
    
    except Exception as e:
        logger.error(f'Error sending batch reports: {str(e)}')
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
