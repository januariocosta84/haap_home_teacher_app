from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from core.models import User, Child, TeacherActivityLog
from preschools.models import PreschoolTeacher, Preschool
from equipment.models import Equipment, EquipmentType
from ticket.models import SupportTicket

@login_required
def moe_admin_dashboard(request):
    if request.user.role != 'moe_admin':
        return redirect('core:login')
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
    if request.user.role != 'municipality_analyst':
        return redirect('core:moe_admin_dashboard')
    user = request.user
    municipality = user.municipality

    children_list = Child.objects.filter(parent__municipality=municipality)
    parents_list = User.objects.filter(role="parent", municipality=municipality)
    teachers_list = User.objects.filter(role="teacher", municipality=municipality)
    teacher_logs = (
        TeacherActivityLog.objects
        .select_related("teacher", "preschool")
        .filter(preschool__municipality=municipality)
        .order_by("-created_at")[:100]
    )

    context = {
        "municipality": municipality,
        "children_count": children_list.count(),
        "parents_count": parents_list.count(),
        "teachers_count": teachers_list.count(),
        "teacher_logs_count": TeacherActivityLog.objects.filter(preschool__municipality=municipality).count(),
        "children_list": children_list,
        "parents_list": parents_list,
        "teachers_list": teachers_list,
        "teacher_logs": teacher_logs,
        "log_status_choices": [],
    }
    return render(request, "dashboards/municipality_dashboard.html", context)

@login_required
def equipment_dashboard(request):
    if request.user.role not in ('moe_admin', 'moe_auditing', 'municipality_analyst'):
        return redirect('core:login')

    types = EquipmentType.objects.all().order_by('name')

    # ── Per-type summary ──────────────────────────────────────────
    type_stats = []
    for t in types:
        qs = Equipment.objects.filter(equipment_type=t)
        type_stats.append({
            'type': t,
            'total':    qs.count(),
            'active':   qs.filter(status='active').count(),
            'inactive': qs.filter(status='inactive').count(),
            'damaged':  qs.filter(status='damaged').count(),
            'retired':  qs.filter(status='retired').count(),
            'assigned': qs.filter(preschool__isnull=False).count(),
            'unassigned': qs.filter(preschool__isnull=True).count(),
        })

    # ── Overall totals ────────────────────────────────────────────
    all_eq = Equipment.objects.all()
    totals = {
        'total':      all_eq.count(),
        'active':     all_eq.filter(status='active').count(),
        'inactive':   all_eq.filter(status='inactive').count(),
        'damaged':    all_eq.filter(status='damaged').count(),
        'retired':    all_eq.filter(status='retired').count(),
        'assigned':   all_eq.filter(preschool__isnull=False).count(),
        'unassigned': all_eq.filter(preschool__isnull=True).count(),
    }

    # ── Per-municipality breakdown ────────────────────────────────
    mun_rows = (
        Equipment.objects
        .filter(preschool__municipality__isnull=False)
        .values('preschool__municipality__name', 'equipment_type__name')
        .annotate(n=Count('id'))
        .order_by('preschool__municipality__name', 'equipment_type__name')
    )
    # Build a dict: {mun_name: {type_name: count}}
    mun_dict = {}
    type_names = [t.name for t in types]
    for row in mun_rows:
        mun = row['preschool__municipality__name']
        typ = row['equipment_type__name']
        if mun not in mun_dict:
            mun_dict[mun] = {t: 0 for t in type_names}
        mun_dict[mun][typ] = row['n']

    mun_table = [
        {
            'name': mun,
            'counts_list': [counts.get(t, 0) for t in type_names],
            'total': sum(counts.values()),
        }
        for mun, counts in sorted(mun_dict.items())
    ]

    # ── Recent assignments ────────────────────────────────────────
    recent = (
        Equipment.objects
        .filter(preschool__isnull=False)
        .select_related('equipment_type', 'preschool__municipality')
        .order_by('-updated_at')[:20]
    )

    context = {
        'type_stats':  type_stats,
        'type_names':  type_names,
        'totals':      totals,
        'mun_table':   mun_table,
        'recent':      recent,
    }
    return render(request, 'dashboards/equipment_dashboard.html', context)


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
