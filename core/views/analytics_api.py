from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.db.models import Count, Q
from datetime import datetime, timedelta
from core.models import ActivityResult, User

@require_GET
def trend_data_api(request):
    """
    Returns aggregated trend data for charts
    Query params: municipality, outcome, period (week/month/quarter/year)
    """
    user = request.user
    municipality = request.GET.get('municipality')
    outcome = request.GET.get('outcome')
    period = request.GET.get('period', 'month')
    
    # Base queryset with role-based access
    queryset = ActivityResult.objects.select_related('student', 'student__parent')
    
    if user.role == 'parent':
        queryset = queryset.filter(student__parent=user)
    elif user.role in ['municipality_analyst', 'teacher']:
        queryset = queryset.filter(student__parent__municipality=user.municipality)
    elif user.role != 'moe_admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Apply filters
    if municipality:
        queryset = queryset.filter(student__parent__municipality=municipality)
    if outcome:
        queryset = queryset.filter(activity_result__icontains=outcome)
    
    # Calculate date range
    end_date = datetime.now()
    if period == 'week':
        start_date = end_date - timedelta(days=7)
    elif period == 'quarter':
        start_date = end_date - timedelta(days=90)
    elif period == 'year':
        start_date = end_date - timedelta(days=365)
    else:  # month
        start_date = end_date - timedelta(days=30)
    
    queryset = queryset.filter(created_at__range=[start_date, end_date])
    
    # Aggregate by date
    trends = queryset.extra(
        select={'date': 'DATE(created_at)'}
    ).values('date').annotate(
        total_count=Count('id'),
        success_count=Count('id', filter=Q(activity_result__isnull=False) & ~Q(activity_result='') & ~Q(activity_result='Tentadu'))
    ).order_by('date')
    
    # Calculate totals
    total_children = queryset.values('student').distinct().count()
    achieved = queryset.filter(activity_result__isnull=False).exclude(activity_result='').exclude(activity_result='Tentadu').count()
    achievement_rate = (achieved / queryset.count() * 100) if queryset.count() > 0 else 0
    
    return JsonResponse({
        'trends': list(trends),
        'summary': {
            'total_children': total_children,
            'total_activities': queryset.count(),
            'achieved': achieved,
            'achievement_rate': round(achievement_rate, 1),
            'period': period
        }
    })

@require_GET
def summary_stats_api(request):
    """Returns current summary statistics based on active filters"""
    user = request.user
    queryset = ActivityResult.objects.select_related('student', 'student__parent')
    
    # Role-based filtering
    if user.role == 'parent':
        queryset = queryset.filter(student__parent=user)
    elif user.role in ['municipality_analyst', 'teacher']:
        queryset = queryset.filter(student__parent__municipality=user.municipality)
    elif user.role != 'moe_admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Apply filters from request
    municipality = request.GET.get('municipality')
    if municipality:
        queryset = queryset.filter(student__parent__municipality=municipality)
    
    total = queryset.count()
    achieved = queryset.filter(activity_result__isnull=False).exclude(activity_result='').exclude(activity_result='Tentadu').count()
    rate = (achieved / total * 100) if total > 0 else 0
    
    return JsonResponse({
        'total': total,
        'achieved': achieved,
        'rate': round(rate, 1)
    })

@require_GET
def get_municipalities_api(request):
    """Returns list of municipalities for filter dropdown"""
    user = request.user
    
    municipalities = []
    
    if user.role == 'moe_admin':
        # MOE admin sees all municipalities
        municipalities = User.objects.filter(
            role__in=['municipality_analyst', 'teacher']
        ).values_list('municipality', flat=True).distinct().order_by('municipality')
    
    elif user.role in ['municipality_analyst', 'teacher']:
        # Analyst/teacher only sees their own municipality
        municipalities = [user.municipality]
    
    elif user.role == 'parent':
        # Parent sees their own municipality
        municipalities = [user.municipality]
    
    return JsonResponse({
        'municipalities': list(municipalities)
    })