import uuid

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.generic import ListView
from django.core.exceptions import PermissionDenied
from django.template.loader import render_to_string

from core.models import ActivityResult, User, Child

def is_valid_uuid(value):
    try:
        uuid.UUID(str(value))
        return True
    except (ValueError, TypeError):
        return False


@login_required
def AppUsageLogListView(request):
    user = request.user
    queryset = (
        ActivityResult.objects
        .select_related("student", "student__parent")
        .order_by("-created_at")
    )
    # 🔍 Activity search
    activity = request.GET.get("activity")
    if activity:
        queryset = queryset.filter(activity_name__icontains=activity)

    # 🔐 ROLE-BASED ACCESS CONTROL
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

    # ✅ SKIP EMPTY SID + PID
    queryset = queryset.filter(
        student__isnull=False,
        student__parent__isnull=False
    )
    

    # 🎯 Parent filter
    parent_id = request.GET.get("parent")
    if parent_id and is_valid_uuid(parent_id):
        queryset = queryset.filter(student__parent__id=parent_id)

    # 🎯 Student filter
    student_id = request.GET.get("student")
    if student_id and is_valid_uuid(student_id):
        queryset = queryset.filter(student__id=student_id)

    # 📄 Pagination
            # paginator = Paginator(queryset, 10)
            # page_number = request.GET.get("page")
            # page_obj = paginator.get_page(page_number)
    
    # Split category1 into tema and tipu
    logs_with_split = []
    for log in queryset:
        if log.category1 and '-' in log.category1:
            parts = log.category1.split('-', 1)  # Split only on first dash
            log.tema = parts[0].strip()
            log.tipu = parts[1].strip() if len(parts) > 1 else ''
        else:
            log.tema = log.category1 or ''
            log.tipu = ''
        logs_with_split.append(log)
    
    context = {
        "logs": logs_with_split,
        "page_obj": None,
        "paginator": None,
        "is_paginated": False,
    }
    # 👇 ADD THIS BLOCK
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string(
            "partials/logs_body.html",
            context,   # you already have "logs" inside
            request=request
        )
        return JsonResponse({"html": html})

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

        # 🔐 ownership check
        if self.child.parent != request.user:
            raise PermissionDenied("You are not allowed to view this child.")

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = ActivityResult.objects.filter(
            student=self.child,
            parent=self.request.user
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
