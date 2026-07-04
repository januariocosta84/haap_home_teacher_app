import uuid
from datetime import datetime, timedelta
import csv
from io import BytesIO

from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.generic import ListView
from django.core.exceptions import PermissionDenied
from django.template.loader import render_to_string
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors

from core.models import ActivityResult, TeacherActivityLog, User, Child
from klase.models import ClassroomChild

def is_valid_uuid(value):
    try:
        uuid.UUID(str(value))
        return True
    except (ValueError, TypeError):
        return False


PAGE_SIZE = 50  # rows per page


@login_required
def AppUsageLogListView(request):
    user = request.user

    # ── Fix N+1: ActivityResult has two parent paths:
    #   1. .parent (direct FK, db_column='pid') — used by template for location fields
    #   2. .student.parent (via Child FK) — used for role-based filtering
    # Both chains need full select_related to avoid per-row queries.
    queryset = (
        ActivityResult.objects
        .select_related(
            "parent",
            "parent__municipality",
            "parent__administrative_post",
            "parent__suco",
            "parent__aldeia",
            "student",
            "student__parent",
            "student__parent__municipality",
            "student__parent__administrative_post",
            "student__parent__suco",
            "student__parent__aldeia",
        )
        .order_by("-created_at")
    )

    # ── Role-based access control ────────────────────────────────────────────
    if user.role == "parent":
        queryset = queryset.filter(student__parent=user)
    elif user.role == "municipality_analyst":
        queryset = queryset.filter(
            student__parent__municipality=user.municipality
        )
    elif user.role == "teacher":
        queryset = queryset.filter(
            student__classroom_history__classroom__teacher=user,
            student__classroom_history__is_active=True
        ).distinct()
    elif user.role == "moe_admin":
        pass
    else:
        queryset = ActivityResult.objects.none()

    # ── Skip rows with no student/parent ────────────────────────────────────
    queryset = queryset.filter(
        student__isnull=False,
        student__parent__isnull=False
    )

    # ── Server-side filters ──────────────────────────────────────────────────
    activity = request.GET.get("activity", "").strip()
    if activity:
        queryset = queryset.filter(activity_name__icontains=activity)

    search_q = request.GET.get("q", "").strip()
    if search_q:
        queryset = queryset.filter(
            Q(activity_name__icontains=search_q)
            | Q(student__first_name__icontains=search_q)
            | Q(student__parent__first_name__icontains=search_q)
            | Q(student__parent__last_name__icontains=search_q)
        )

    parent_id = request.GET.get("parent")
    if parent_id and is_valid_uuid(parent_id):
        queryset = queryset.filter(student__parent__id=parent_id)

    student_id = request.GET.get("student")
    if student_id and is_valid_uuid(student_id):
        queryset = queryset.filter(student__id=student_id)

    date_from = request.GET.get("date_from", "").strip()
    if date_from:
        try:
            queryset = queryset.filter(
                created_at__gte=datetime.strptime(date_from, "%Y-%m-%d")
            )
        except ValueError:
            date_from = ""

    date_to = request.GET.get("date_to", "").strip()
    if date_to:
        try:
            queryset = queryset.filter(
                created_at__lte=datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
            )
        except ValueError:
            date_to = ""

    # ── Aggregate stats from the full filtered queryset (before pagination) ─
    from django.db.models import Count
    stats = queryset.aggregate(
        total_activities=Count("id"),
        unique_students=Count("student", distinct=True),
        achieved=Count(
            "id",
            filter=Q(activity_result__isnull=False)
            & ~Q(activity_result="")
            & ~Q(activity_result="Tentadu"),
        ),
    )
    total_activities = stats["total_activities"]
    unique_students = stats["unique_students"]
    achieved = stats["achieved"]
    rate = round(achieved / total_activities * 100, 1) if total_activities else 0

    # ── Server-side pagination ───────────────────────────────────────────────
    paginator = Paginator(queryset, PAGE_SIZE)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # ── Split category1 for current page only (O(page_size) not O(total)) ──
    logs_with_split = []
    for log in page_obj:
        if log.category1 and "-" in log.category1:
            parts = log.category1.split("-", 1)
            log.tema = parts[0].strip()
            log.tipu = parts[1].strip() if len(parts) > 1 else ""
        else:
            log.tema = log.category1 or ""
            log.tipu = ""
        logs_with_split.append(log)

    context = {
        "logs": logs_with_split,
        "page_obj": page_obj,
        "paginator": paginator,
        "is_paginated": paginator.num_pages > 1,
        "total_activities": total_activities,
        "unique_students": unique_students,
        "total_achieved": achieved,
        "achievement_rate": rate,
        "search_q": search_q,
        "activity_filter": activity,
        "date_from": date_from,
        "date_to": date_to,
    }

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string("partials/logs_body.html", context, request=request)
        return JsonResponse({
            "html": html,
            "stats": {
                "total_activities": total_activities,
                "unique_students": unique_students,
                "total_achieved": achieved,
                "achievement_rate": rate,
            },
        })
    return render(request, "dashboards/logs.html", context)

class ChildActivityView(LoginRequiredMixin, ListView):
    model = ActivityResult
    template_name = "dashboards/child_activity.html"
    context_object_name = "activities"
    paginate_by = 10  # 👈 number of records per page

    def dispatch(self, request, *args, **kwargs):
        """
        Security check BEFORE loading the page
        """
        child_id = self.kwargs["child_id"]

        self.child = get_object_or_404(Child, id=child_id)

        is_parent = self.child.parent == request.user
        is_connected_teacher = (
            request.user.role == "teacher"
            and ClassroomChild.objects.filter(
                child=self.child,
                classroom__teacher=request.user,
                is_active=True
            ).exists()
        )
        is_moe_admin = request.user.role == "moe_admin"

        if not (is_parent or is_connected_teacher or is_moe_admin):
            raise PermissionDenied("Ita la iha permisaun atu haree labarik ida ne'e.")

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = ActivityResult.objects.filter(
            student=self.child,
            parent=self.child.parent
        ).order_by("-created_at")

        # Split category1 into two attributes
        for obj in queryset:
            if obj.category1:
                if '-' in obj.category1:
                    parts = obj.category1.split('-')
                    obj.cat1_left = parts[0].strip()
                    obj.cat1_right = parts[1].strip() if len(parts) > 1 else ''
                else:
                    # Only one value, put it in left column
                    obj.cat1_left = obj.category1.strip()
                    obj.cat1_right = ''
            else:
                obj.cat1_left = ''
                obj.cat1_right = ''

            # Optional: split category2 and category3 similarly if needed
            obj.cat2_left = obj.category2 or ''
            obj.cat3_left = obj.category3 or ''

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["child"] = self.child
        return context


class TeacherActivityLogListView(LoginRequiredMixin, ListView):
    model = TeacherActivityLog
    template_name = "dashboards/teacher_logs.html"
    context_object_name = "logs"

    def get_queryset(self):
        user = self.request.user
        queryset = TeacherActivityLog.objects.select_related("preschool", "teacher").order_by("-created_at")

        if user.role == "teacher":
            queryset = queryset.filter(teacher=user)
        elif user.role == "municipality_analyst":
            queryset = queryset.filter(preschool__municipality=user.municipality)
        elif user.role == "moe_admin":
            pass  # See all logs
        else:
            return queryset.none()

        # Apply filters
        teacher_id = self.request.GET.get('teacher')
        if teacher_id and user.role in ['moe_admin', 'municipality_analyst']:
            queryset = queryset.filter(teacher_id=teacher_id)

        preschool_id = self.request.GET.get('preschool')
        if preschool_id:
            queryset = queryset.filter(preschool_id=preschool_id)

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        date_from = self.request.GET.get('date_from')
        if date_from:
            try:
                queryset = queryset.filter(created_at__gte=datetime.strptime(date_from, '%Y-%m-%d'))
            except ValueError:
                pass

        date_to = self.request.GET.get('date_to')
        if date_to:
            try:
                queryset = queryset.filter(created_at__lte=datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1))
            except ValueError:
                pass

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["page_title"] = "Teacher Logs"

        if user.role == "moe_admin":
            context["teachers"] = User.objects.filter(role='teacher').order_by('first_name')
            from preschools.models import Preschool
            context["preschools"] = Preschool.objects.all().order_by('name')
        elif user.role == "municipality_analyst":
            context["teachers"] = User.objects.filter(role='teacher', municipality=user.municipality).order_by('first_name')
            from preschools.models import Preschool
            context["preschools"] = Preschool.objects.filter(municipality=user.municipality).order_by('name')

        context["filter_teacher"] = self.request.GET.get('teacher', '')
        context["filter_preschool"] = self.request.GET.get('preschool', '')
        context["filter_status"] = self.request.GET.get('status', '')
        context["filter_date_from"] = self.request.GET.get('date_from', '')
        context["filter_date_to"] = self.request.GET.get('date_to', '')

        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            html = render_to_string(
                "partials/teacher_logs_body.html",
                context,
                request=self.request
            )
            return JsonResponse({"html": html})
        return super().render_to_response(context, **response_kwargs)

    def get(self, request, *args, **kwargs):
        export_format = request.GET.get('export')
        if export_format == 'csv':
            return self.export_csv()
        elif export_format == 'pdf':
            return self.export_pdf()
        return super().get(request, *args, **kwargs)

    def export_csv(self):
        queryset = self.get_queryset()
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="teacher_logs.csv"'

        writer = csv.writer(response)
        writer.writerow(['Date', 'Teacher', 'Preschool', 'Theme', 'Sub-theme', 'Activity', 'Status'])

        for log in queryset:
            writer.writerow([
                log.created_at.strftime('%Y-%m-%d %H:%M'),
                log.teacher.get_full_name(),
                log.preschool.name if log.preschool else '',
                log.theme or '',
                log.sub_theme or '',
                log.activity_name or '',
                log.get_status_display(),
            ])

        return response

    def export_pdf(self):
        queryset = self.get_queryset()
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()

        # Title
        title = Paragraph("Teacher Activity Logs", styles['Heading1'])
        elements.append(title)
        elements.append(Spacer(1, 0.3 * inch))

        # Table data
        data = [['Date', 'Teacher', 'Preschool', 'Theme', 'Activity', 'Status']]
        for log in queryset:
            data.append([
                log.created_at.strftime('%Y-%m-%d %H:%M'),
                log.teacher.get_full_name()[:15],
                (log.preschool.name if log.preschool else '')[:15],
                (log.theme or '')[:10],
                (log.activity_name or '')[:15],
                log.get_status_display(),
            ])

        # Create table
        table = Table(data, colWidths=[1.0*inch, 1.1*inch, 1.1*inch, 0.9*inch, 0.9*inch, 1.0*inch, 0.9*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))

        elements.append(table)
        doc.build(elements)

        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="teacher_logs.pdf"'
        return response
