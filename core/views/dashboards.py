from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from core.models import User, Child
from preschools.models import PreschoolTeacher, Preschool
from equipment.models import Equipment
from ticket.models import SupportTicket

@login_required
def moe_admin_dashboard(request):
    tickets_qs = SupportTicket.objects.select_related(
        'teacher', 'preschool'
    ).order_by('-created_at')

    context = {
        "all_users": User.objects.count(),
        "parents": User.objects.filter(role="parent").count(),
        "municipality_analysts": User.objects.filter(role="municipality_analyst").count(),
        "children": Child.objects.count(),
        "teachers": User.objects.filter(role="teacher").count(),
        "preschools": Preschool.objects.count(),
        "equipments": Equipment.objects.count(),
        "pending_teacher_requests": PreschoolTeacher.objects.filter(is_active=True, is_approved=False).count(),
        # Ticket stats
        "tickets_total": tickets_qs.count(),
        "tickets_open": tickets_qs.filter(status="open").count(),
        "tickets_in_progress": tickets_qs.filter(status="in_progress").count(),
        "tickets_resolved": tickets_qs.filter(status__in=["resolved", "closed"]).count(),
        # Recent tickets for list
        "recent_tickets": tickets_qs[:10],
    }
    return render(request, "dashboards/moe_admin.html", context=context)


@login_required
def municipality_dashboard(request):
    user = request.user
    municipality = user.municipality

    children_list = Child.objects.filter(parent__municipality=municipality)
    parents_list = User.objects.filter(role="parent", municipality=municipality)
    teachers_list = User.objects.filter(role="teacher", municipality=municipality)

    context = {
        "municipality": municipality,
        "children_count": children_list.count(),
        "parents_count": parents_list.count(),
        "teachers_count": teachers_list.count(),
        "children_list": children_list,
        "parents_list": parents_list,
        "teachers_list": teachers_list,
    }
    return render(request, "dashboards/municipality_dashboard.html", context)

@login_required
def teacher_dashboard(request):
    municipality = request.user.municipality
    children_list = Child.objects.filter(parent__municipality=municipality)
    parents_list = User.objects.filter(role="parent", municipality=municipality)

    context = {
        "municipality": municipality,
        "children_count": children_list.count(),
        "parents_count": parents_list.count(),
        "children_list": children_list,
        "parents_list": parents_list,
    }
    return render(request, "dashboards/teacher_dashboard.html", context)
