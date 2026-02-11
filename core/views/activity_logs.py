import uuid

from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.generic import ListView
from django.core.exceptions import PermissionDenied

from core.models import ActivityResult, User, Child

def is_valid_uuid(value):
    try:
        uuid.UUID(str(value))
        return True
    except Exception:
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
        # Parent sees ONLY their own children
        queryset = queryset.filter(student__parent=user)

    elif user.role in ["municipality_analyst", "teacher"]:
        queryset = queryset.filter(
            student__parent__municipality=user.municipality
        )

    elif user.role == "moe_admin":
        # Full access
        pass

    else:
        queryset = ActivityResult.objects.none()

    # 🎯 Parent filter
    parent_id = request.GET.get("parent")
    if parent_id and is_valid_uuid(parent_id):
        queryset = queryset.filter(student__parent__id=parent_id)

    # 🎯 Student filter
    student_id = request.GET.get("student")
    print("Student",student_id)
    if student_id and is_valid_uuid(student_id):
        queryset = queryset.filter(student__id=student_id)

    # 📄 Pagination
    paginator = Paginator(queryset, 10)  # same as paginate_by = 10
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "logs": page_obj,        # matches context_object_name
        "page_obj": page_obj,
        "paginator": paginator,
        "is_paginated": page_obj.has_other_pages(),
    }

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
        return ActivityResult.objects.filter(
            student=self.child,
            parent=self.request.user
        ).order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["child"] = self.child
        return context
