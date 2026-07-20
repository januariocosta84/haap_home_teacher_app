import uuid
from datetime import datetime, timedelta
from io import BytesIO

from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.views.generic import ListView
from django.core.exceptions import PermissionDenied
from django.template.loader import render_to_string

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

        from django.db.models import Count, Q
        stats = ActivityResult.objects.filter(
            student=self.child, parent=self.child.parent
        ).aggregate(
            total=Count("id"),
            achieved=Count("id", filter=Q(activity_result__isnull=False) & ~Q(activity_result="") & ~Q(activity_result="Tentadu")),
            attempted=Count("id", filter=Q(activity_result="Tentadu")),
        )
        context["stat_total"] = stats["total"]
        context["stat_achieved"] = stats["achieved"]
        context["stat_attempted"] = stats["attempted"]
        context["stat_rate"] = round(stats["achieved"] / stats["total"] * 100) if stats["total"] else 0

        return context


class TeacherActivityLogListView(LoginRequiredMixin, ListView):
    model = TeacherActivityLog
    template_name = "dashboards/teacher_logs.html"
    context_object_name = "logs"

    def get_queryset(self):
        from django.db.models import OuterRef, Subquery
        user = self.request.user

        daily_visits = (
            TeacherActivityLog.objects
            .filter(
                teacher=OuterRef('teacher'),
                sub_theme=OuterRef('sub_theme'),
                activity_date=OuterRef('activity_date'),
            )
            .values('teacher')
            .annotate(cnt=Count('id'))
            .values('cnt')
        )

        queryset = (
            TeacherActivityLog.objects
            .select_related("preschool", "teacher")
            .annotate(vizita=Subquery(daily_visits))
            .order_by("-created_at")
        )

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

        # Status summary: pivot per teacher → sub-theme rows × date columns
        from collections import defaultdict
        summary_qs = (
            self.get_queryset()
            .exclude(sub_theme__isnull=True)
            .exclude(sub_theme='')
            .values(
                'teacher_id',
                'teacher__first_name',
                'teacher__last_name',
                'activity_date',
                'sub_theme',
            )
            .annotate(visits=Count('id'))
            .order_by('teacher__first_name', 'teacher__last_name', 'sub_theme', '-activity_date')
        )

        pivot = {}
        for row in summary_qs:
            tid = str(row['teacher_id'])
            name = f"{row['teacher__first_name']} {row['teacher__last_name']}"
            date = row['activity_date']
            sub  = row['sub_theme']
            if tid not in pivot:
                pivot[tid] = {'name': name, 'dates': set(), 'rows': defaultdict(dict)}
            pivot[tid]['dates'].add(date)
            pivot[tid]['rows'][sub][date] = row['visits']

        status_summary = []
        for tid, tdata in pivot.items():
            dates = sorted(tdata['dates'], reverse=True)
            sub_rows = []
            total_by_date = {d: 0 for d in dates}
            for sub_theme, day_counts in sorted(tdata['rows'].items()):
                cells = []
                row_total = 0
                for d in dates:
                    v = day_counts.get(d, 0)
                    cells.append(v)
                    row_total += v
                    total_by_date[d] += v
                sub_rows.append({
                    'sub_theme': sub_theme,
                    'cells': cells,
                    'total': row_total,
                })
            status_summary.append({
                'name': tdata['name'],
                'dates': dates,
                'sub_rows': sub_rows,
                'totals': [total_by_date[d] for d in dates],
                'grand_total': sum(total_by_date.values()),
            })

        context['status_summary'] = status_summary
        context['active_tab'] = self.request.GET.get('tab', 'status')

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
        if export_format == 'excel':
            return self.export_excel()
        elif export_format == 'pdf':
            return self.export_pdf()
        return super().get(request, *args, **kwargs)

    # ── shared pivot builder ───────────────────────────────────────────────
    def _build_pivot(self):
        from collections import defaultdict
        summary_qs = (
            self.get_queryset()
            .exclude(sub_theme__isnull=True).exclude(sub_theme='')
            .values('teacher_id','teacher__first_name','teacher__last_name',
                    'activity_date','sub_theme')
            .annotate(visits=Count('id'))
            .order_by('teacher__first_name','teacher__last_name','sub_theme','-activity_date')
        )
        pivot = {}
        for row in summary_qs:
            tid  = str(row['teacher_id'])
            name = f"{row['teacher__first_name']} {row['teacher__last_name']}"
            date = row['activity_date']
            sub  = row['sub_theme']
            if tid not in pivot:
                pivot[tid] = {'name': name, 'dates': set(), 'rows': defaultdict(dict)}
            pivot[tid]['dates'].add(date)
            pivot[tid]['rows'][sub][date] = row['visits']

        result = []
        for tdata in pivot.values():
            dates = sorted(tdata['dates'], reverse=True)
            sub_rows, total_by_date = [], {d: 0 for d in dates}
            for sub_theme, day_counts in sorted(tdata['rows'].items()):
                cells, row_total = [], 0
                for d in dates:
                    v = day_counts.get(d, 0)
                    cells.append(v); row_total += v; total_by_date[d] += v
                sub_rows.append({'sub_theme': sub_theme, 'cells': cells, 'total': row_total})
            result.append({
                'name': tdata['name'], 'dates': dates, 'sub_rows': sub_rows,
                'totals': [total_by_date[d] for d in dates],
                'grand_total': sum(total_by_date.values()),
            })
        return result

    # ── Excel export ───────────────────────────────────────────────────────
    def export_excel(self):
        import openpyxl
        from openpyxl.styles import (Font, PatternFill, Alignment,
                                     Border, Side, GradientFill)
        from openpyxl.utils import get_column_letter
        from datetime import date as dt_date

        pivot = self._build_pivot()
        wb = openpyxl.Workbook()

        # ── colours ──
        BLUE_DARK  = "1D4ED8"
        BLUE_MID   = "2563EB"
        BLUE_LIGHT = "DBEAFE"
        BLUE_PALE  = "EFF6FF"
        WHITE      = "FFFFFF"
        GREY_HEAD  = "F8FAFC"
        GREY_LINE  = "E2E8F0"
        TOTAL_BG   = "BFDBFE"
        GREEN_CELL = "DCFCE7"
        GREEN_TEXT = "166534"

        thin = Side(style='thin', color=GREY_LINE)
        med  = Side(style='medium', color=BLUE_DARK)
        border_thin  = Border(left=thin, right=thin, top=thin, bottom=thin)
        border_head  = Border(left=med, right=med, top=med, bottom=med)

        def _cell(ws, row, col, value, bold=False, fg=None, bg=None,
                  align='left', size=10, border=None, wrap=False):
            c = ws.cell(row=row, column=col, value=value)
            c.font = Font(name='Calibri', bold=bold, color=fg or "1E293B", size=size)
            if bg:
                c.fill = PatternFill("solid", fgColor=bg)
            c.alignment = Alignment(horizontal=align, vertical='center',
                                    wrap_text=wrap)
            if border:
                c.border = border
            return c

        # ══ Sheet 1: Pivot (Status Sub-Tema) ═════════════════════════════
        ws1 = wb.active
        ws1.title = "Status Sub-Tema"
        ws1.sheet_view.showGridLines = False

        row = 1
        # Cover header
        ws1.row_dimensions[row].height = 40
        c = ws1.cell(row=row, column=1,
                     value="HAAP — Relatóriu Status Sub-Tema Profesór")
        c.font = Font(name='Calibri', bold=True, size=18, color=WHITE)
        c.fill = PatternFill("solid", fgColor=BLUE_MID)
        c.alignment = Alignment(horizontal='left', vertical='center')
        ws1.merge_cells(start_row=row, start_column=1, end_row=row, end_column=12)
        row += 1

        ws1.row_dimensions[row].height = 20
        c = ws1.cell(row=row, column=1,
                     value=f"Gerado: {dt_date.today().strftime('%d %B %Y')}")
        c.font = Font(name='Calibri', size=10, color="64748B")
        c.fill = PatternFill("solid", fgColor=BLUE_PALE)
        c.alignment = Alignment(horizontal='left', vertical='center')
        ws1.merge_cells(start_row=row, start_column=1, end_row=row, end_column=12)
        row += 2

        for teacher in pivot:
            n_dates = len(teacher['dates'])
            total_cols = 1 + n_dates + 1   # sub-theme + dates + total

            # Teacher name banner
            ws1.row_dimensions[row].height = 28
            c = ws1.cell(row=row, column=1, value=f"  {teacher['name']}")
            c.font = Font(name='Calibri', bold=True, size=13, color=WHITE)
            c.fill = PatternFill("solid", fgColor=BLUE_DARK)
            c.alignment = Alignment(horizontal='left', vertical='center')
            ws1.merge_cells(start_row=row, start_column=1,
                            end_row=row, end_column=total_cols)
            row += 1

            # Column headers: Sub-Tema | date... | Total
            ws1.row_dimensions[row].height = 32
            _cell(ws1, row, 1, "Sub-Tema", bold=True, fg=BLUE_DARK,
                  bg=BLUE_LIGHT, align='center', border=border_thin)
            ws1.column_dimensions['A'].width = 20

            for ci, d in enumerate(teacher['dates'], start=2):
                day_str = d.strftime('%d/%m')
                dow_str = d.strftime('%a')
                c = ws1.cell(row=row, column=ci, value=f"{day_str}\n{dow_str}")
                c.font = Font(name='Calibri', bold=True, size=9, color=BLUE_DARK)
                c.fill = PatternFill("solid", fgColor=BLUE_LIGHT)
                c.alignment = Alignment(horizontal='center', vertical='center',
                                        wrap_text=True)
                c.border = border_thin
                ws1.column_dimensions[get_column_letter(ci)].width = 10

            total_col = n_dates + 2
            _cell(ws1, row, total_col, "Total", bold=True, fg=WHITE,
                  bg=BLUE_MID, align='center', border=border_thin)
            ws1.column_dimensions[get_column_letter(total_col)].width = 10
            row += 1

            # Sub-theme rows
            for ri, sr in enumerate(teacher['sub_rows']):
                ws1.row_dimensions[row].height = 20
                bg_row = WHITE if ri % 2 == 0 else GREY_HEAD
                _cell(ws1, row, 1, sr['sub_theme'], bold=True,
                      fg=BLUE_DARK, bg=bg_row, align='left', border=border_thin)
                for ci, v in enumerate(sr['cells'], start=2):
                    cell_bg = GREEN_CELL if v > 0 else bg_row
                    cell_fg = GREEN_TEXT if v > 0 else "CBD5E1"
                    c = ws1.cell(row=row, column=ci, value=v if v > 0 else None)
                    c.font = Font(name='Calibri', bold=(v > 0), size=11,
                                  color=(cell_fg if v == 0 else GREEN_TEXT))
                    c.fill = PatternFill("solid", fgColor=cell_bg)
                    c.alignment = Alignment(horizontal='center', vertical='center')
                    c.border = border_thin
                # Row total
                c = ws1.cell(row=row, column=total_col, value=sr['total'])
                c.font = Font(name='Calibri', bold=True, size=11, color=BLUE_DARK)
                c.fill = PatternFill("solid", fgColor=BLUE_PALE)
                c.alignment = Alignment(horizontal='center', vertical='center')
                c.border = border_thin
                row += 1

            # Totals row
            ws1.row_dimensions[row].height = 22
            _cell(ws1, row, 1, "TOTAL", bold=True, fg=WHITE,
                  bg=BLUE_MID, align='center', border=border_thin)
            for ci, t in enumerate(teacher['totals'], start=2):
                c = ws1.cell(row=row, column=ci, value=t)
                c.font = Font(name='Calibri', bold=True, size=11, color=BLUE_DARK)
                c.fill = PatternFill("solid", fgColor=TOTAL_BG)
                c.alignment = Alignment(horizontal='center', vertical='center')
                c.border = border_thin
            c = ws1.cell(row=row, column=total_col, value=teacher['grand_total'])
            c.font = Font(name='Calibri', bold=True, size=13, color=WHITE)
            c.fill = PatternFill("solid", fgColor=BLUE_DARK)
            c.alignment = Alignment(horizontal='center', vertical='center')
            c.border = border_thin
            row += 3   # gap between teachers

        # ══ Sheet 2: Detail log ═══════════════════════════════════════════
        ws2 = wb.create_sheet("Rejistu Detalhadu")
        ws2.sheet_view.showGridLines = False

        headers = ["Data", "Oras", "Profesór", "Pre-Eskolár",
                   "Tema", "Sub-Tema", "Atividade", "Vizita"]
        col_widths = [12, 8, 22, 22, 18, 18, 28, 8]

        # Sheet title
        ws2.row_dimensions[1].height = 36
        c = ws2.cell(row=1, column=1, value="HAAP — Rejistu Detalhadu Atividade Profesór")
        c.font = Font(name='Calibri', bold=True, size=14, color=WHITE)
        c.fill = PatternFill("solid", fgColor=BLUE_MID)
        c.alignment = Alignment(horizontal='left', vertical='center')
        ws2.merge_cells(start_row=1, start_column=1, end_row=1,
                        end_column=len(headers))

        ws2.row_dimensions[2].height = 18
        c = ws2.cell(row=2, column=1,
                     value=f"Gerado: {dt_date.today().strftime('%d %B %Y')}")
        c.font = Font(name='Calibri', size=9, color="64748B")
        c.fill = PatternFill("solid", fgColor=BLUE_PALE)
        c.alignment = Alignment(horizontal='left', vertical='center')
        ws2.merge_cells(start_row=2, start_column=1, end_row=2,
                        end_column=len(headers))

        # Header row
        ws2.row_dimensions[3].height = 26
        for ci, (h, w) in enumerate(zip(headers, col_widths), start=1):
            c = ws2.cell(row=3, column=ci, value=h)
            c.font = Font(name='Calibri', bold=True, size=10, color=WHITE)
            c.fill = PatternFill("solid", fgColor=BLUE_DARK)
            c.alignment = Alignment(horizontal='center', vertical='center')
            c.border = border_thin
            ws2.column_dimensions[get_column_letter(ci)].width = w

        # Data rows
        detail_qs = self.get_queryset()
        for ri, log in enumerate(detail_qs, start=4):
            bg = WHITE if ri % 2 == 0 else GREY_HEAD
            ws2.row_dimensions[ri].height = 18
            row_data = [
                log.created_at.strftime('%d/%m/%Y'),
                log.created_at.strftime('%H:%M'),
                log.teacher.get_full_name(),
                log.preschool.name if log.preschool else '—',
                log.theme or '—',
                log.sub_theme or '—',
                log.activity_name or '—',
                getattr(log, 'vizita', '—'),
            ]
            for ci, val in enumerate(row_data, start=1):
                c = ws2.cell(row=ri, column=ci, value=val)
                c.font = Font(name='Calibri', size=9, color="334155")
                c.fill = PatternFill("solid", fgColor=bg)
                c.alignment = Alignment(horizontal='center' if ci in (1,2,8) else 'left',
                                        vertical='center')
                c.border = border_thin

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="haap_teacher_report.xlsx"'
        return response

    # ── PDF export ─────────────────────────────────────────────────────────
    def export_pdf(self):
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                        Paragraph, Spacer, HRFlowable,
                                        PageBreak, KeepTogether)
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch, cm
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        from datetime import date as dt_date

        pivot   = self._build_pivot()
        buffer  = BytesIO()
        PAGE     = landscape(A4)
        MARGIN   = 1.5 * cm
        PW       = PAGE[0] - 2 * MARGIN   # usable page width
        doc     = SimpleDocTemplate(
            buffer, pagesize=PAGE,
            leftMargin=MARGIN, rightMargin=MARGIN,
            topMargin=MARGIN, bottomMargin=MARGIN,
        )

        BLUE      = colors.HexColor('#2563EB')
        BLUE_DARK = colors.HexColor('#1D4ED8')
        BLUE_LITE = colors.HexColor('#DBEAFE')
        BLUE_PALE = colors.HexColor('#EFF6FF')
        GREEN     = colors.HexColor('#DCFCE7')
        GREEN_TXT = colors.HexColor('#166534')
        GREY_ROW  = colors.HexColor('#F8FAFC')
        GREY_LINE = colors.HexColor('#E2E8F0')
        WHITE     = colors.white
        TOTAL_BG  = colors.HexColor('#BFDBFE')
        BLUE_ACCENT = colors.HexColor('#93C5FD')

        styles = getSampleStyleSheet()
        s_title = ParagraphStyle('rpt_title', parent=styles['Normal'],
                                 fontSize=18, fontName='Helvetica-Bold',
                                 textColor=WHITE, alignment=TA_LEFT,
                                 leading=22)
        s_sub   = ParagraphStyle('rpt_sub', parent=styles['Normal'],
                                 fontSize=9, fontName='Helvetica',
                                 textColor=BLUE_ACCENT, alignment=TA_LEFT,
                                 leading=13)
        s_date  = ParagraphStyle('rpt_date', parent=styles['Normal'],
                                 fontSize=9, fontName='Helvetica',
                                 textColor=WHITE, alignment=TA_RIGHT,
                                 leading=13)
        s_teacher = ParagraphStyle('rpt_teacher', parent=styles['Normal'],
                                   fontSize=12, fontName='Helvetica-Bold',
                                   textColor=WHITE, alignment=TA_LEFT)
        s_cell  = ParagraphStyle('rpt_cell', parent=styles['Normal'],
                                 fontSize=8, fontName='Helvetica',
                                 textColor=colors.HexColor('#1E293B'))
        s_hdr   = ParagraphStyle('rpt_hdr', parent=styles['Normal'],
                                 fontSize=8, fontName='Helvetica-Bold',
                                 textColor=WHITE, alignment=TA_CENTER)

        def make_header_table():
            left_w  = PW * 0.68
            right_w = PW * 0.32
            title_cell = [
                Paragraph("HAAP", ParagraphStyle(
                    'rpt_logo', parent=styles['Normal'],
                    fontSize=22, fontName='Helvetica-Bold',
                    textColor=WHITE, leading=26)),
                Paragraph("Relatóriu Status Sub-Tema Profesór", s_sub),
            ]
            date_cell = Paragraph(
                f"Gerado em<br/><b>{dt_date.today().strftime('%d %B %Y')}</b>",
                s_date,
            )
            # two-row left cell stacked inside a nested table
            inner = Table(
                [[p] for p in title_cell],
                colWidths=[left_w - 32],
            )
            inner.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), BLUE),
                ('TOPPADDING',    (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                ('LEFTPADDING',   (0,0), (-1,-1), 0),
                ('RIGHTPADDING',  (0,0), (-1,-1), 0),
            ]))
            outer = Table(
                [[inner, date_cell]],
                colWidths=[left_w, right_w],
            )
            outer.setStyle(TableStyle([
                ('BACKGROUND',    (0,0), (-1,-1), BLUE),
                ('TOPPADDING',    (0,0), (-1,-1), 14),
                ('BOTTOMPADDING', (0,0), (-1,-1), 14),
                ('LEFTPADDING',   (0,0), (0,0),   18),
                ('RIGHTPADDING',  (1,0), (1,0),   18),
                ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
                ('LINEBELOW',     (0,0), (-1,-1), 3, BLUE_DARK),
            ]))
            return outer

        elements = [make_header_table(), Spacer(1, 0.5*cm)]

        for ti, teacher in enumerate(pivot):
            n_dates = len(teacher['dates'])
            col_tot_w  = 1.8 * cm
            col_sub_w  = min(4.5 * cm, PW * 0.25)
            remaining  = PW - col_sub_w - col_tot_w
            col_date_w = min(2.4 * cm, remaining / max(n_dates, 1))

            col_widths_pdf = [col_sub_w] + [col_date_w]*n_dates + [col_tot_w]

            # Teacher banner — stretch to full page width
            teacher_banner = Table(
                [[Paragraph(f"  {teacher['name']}", s_teacher)]],
                colWidths=[PW],
            )
            teacher_banner.setStyle(TableStyle([
                ('BACKGROUND',   (0,0), (-1,-1), BLUE_DARK),
                ('TOPPADDING',   (0,0), (-1,-1), 9),
                ('BOTTOMPADDING',(0,0), (-1,-1), 9),
                ('LEFTPADDING',  (0,0), (-1,-1), 12),
                ('RIGHTPADDING', (0,0), (-1,-1), 12),
            ]))

            # Column headers
            hdr_row = [Paragraph("Sub-Tema", s_hdr)]
            for d in teacher['dates']:
                hdr_row.append(Paragraph(
                    f"{d.strftime('%d/%m')}<br/><font size='7'>{d.strftime('%a')}</font>",
                    s_hdr
                ))
            hdr_row.append(Paragraph("Total", s_hdr))

            table_data = [hdr_row]
            ts_cmds = [
                ('BACKGROUND', (0,0), (-1,0), BLUE),
                ('TEXTCOLOR',  (0,0), (-1,0), WHITE),
                ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE',   (0,0), (-1,-1), 8),
                ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
                ('ALIGN',      (0,1), (0,-1), 'LEFT'),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING',(0,0),(-1,-1), 5),
                ('GRID',       (0,0), (-1,-1), 0.5, GREY_LINE),
                ('LEFTPADDING',(0,1),(0,-1), 8),
            ]

            for ri, sr in enumerate(teacher['sub_rows']):
                bg = WHITE if ri % 2 == 0 else GREY_ROW
                data_row = [Paragraph(sr['sub_theme'],
                                      ParagraphStyle('c', parent=s_cell,
                                                     fontName='Helvetica-Bold',
                                                     textColor=BLUE_DARK))]
                for v in sr['cells']:
                    if v > 0:
                        data_row.append(Paragraph(f"<b>{v}</b>",
                                                  ParagraphStyle('cv', parent=s_cell,
                                                                 textColor=GREEN_TXT,
                                                                 alignment=TA_CENTER)))
                    else:
                        data_row.append(Paragraph("—",
                                                  ParagraphStyle('ce', parent=s_cell,
                                                                 textColor=colors.HexColor('#CBD5E1'),
                                                                 alignment=TA_CENTER)))
                data_row.append(Paragraph(f"<b>{sr['total']}</b>",
                                          ParagraphStyle('ct', parent=s_cell,
                                                         textColor=BLUE_DARK,
                                                         alignment=TA_CENTER)))
                table_data.append(data_row)
                actual_row = ri + 1
                ts_cmds.append(('BACKGROUND', (0, actual_row), (-1, actual_row), bg))
                for ci, v in enumerate(sr['cells'], start=1):
                    if v > 0:
                        ts_cmds.append(('BACKGROUND', (ci, actual_row), (ci, actual_row), GREEN))
                ts_cmds.append(('BACKGROUND', (n_dates+1, actual_row), (n_dates+1, actual_row), BLUE_PALE))

            # Totals row
            totals_row = [Paragraph("<b>TOTAL</b>",
                                    ParagraphStyle('tt', parent=s_cell,
                                                   textColor=WHITE, alignment=TA_CENTER))]
            for t_val in teacher['totals']:
                totals_row.append(Paragraph(f"<b>{t_val}</b>",
                                            ParagraphStyle('tv', parent=s_cell,
                                                           textColor=BLUE_DARK,
                                                           alignment=TA_CENTER)))
            totals_row.append(Paragraph(f"<b>{teacher['grand_total']}</b>",
                                        ParagraphStyle('tg', parent=s_cell,
                                                       textColor=WHITE, alignment=TA_CENTER)))
            table_data.append(totals_row)
            last = len(table_data) - 1
            ts_cmds += [
                ('BACKGROUND', (0, last), (0, last), BLUE),
                ('BACKGROUND', (1, last), (n_dates, last), TOTAL_BG),
                ('BACKGROUND', (n_dates+1, last), (n_dates+1, last), BLUE_DARK),
            ]

            pivot_table = Table(table_data, colWidths=col_widths_pdf,
                                repeatRows=1)
            pivot_table.setStyle(TableStyle(ts_cmds))

            block = KeepTogether([teacher_banner, Spacer(1,0.1*cm),
                                  pivot_table, Spacer(1,0.6*cm)])
            elements.append(block)

            if ti < len(pivot) - 1:
                elements.append(Spacer(1, 0.4*cm))

        doc.build(elements)
        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="haap_teacher_report.pdf"'
        return response
