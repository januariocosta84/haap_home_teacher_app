from django.contrib import messages
from django.shortcuts import redirect
from django.utils.dateparse import parse_date
from django.views.generic import ListView, TemplateView
from django.db.models import Count, Max, Min
from django.db.models.functions import TruncDate
from core.models import Child, Municipality, AdministrativePost, Suco, Aldeia
from klase.models import ClassroomChild
from preschools.models import Preschool

class ChildrenReportView(ListView):
    model = Child
    template_name = "dashboards/children_report.html"
    context_object_name = "children"

    def get_queryset(self):
        queryset = Child.objects.select_related(
            "parent__municipality",
            "parent__administrative_post",
            "parent__suco",
            "parent__aldeia"
        )

        municipality_id = self.request.GET.get("municipality")
        ap_id = self.request.GET.get("administrative_post")
        suco_id = self.request.GET.get("suco")
        aldeia_id = self.request.GET.get("aldeia")

        if municipality_id:
            queryset = queryset.filter(parent__municipality_id=municipality_id)
        if ap_id:
            queryset = queryset.filter(parent__administrative_post_id=ap_id)
        if suco_id:
            queryset = queryset.filter(parent__suco_id=suco_id)
        if aldeia_id:
            queryset = queryset.filter(parent__aldeia_id=aldeia_id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        municipality_id = self.request.GET.get("municipality")
        ap_id = self.request.GET.get("administrative_post")
        suco_id = self.request.GET.get("suco")
        aldeia_id = self.request.GET.get("aldeia")

        context["municipalities"] = Municipality.objects.all().order_by("name")

        if municipality_id:
            context["administrative_posts"] = AdministrativePost.objects.filter(
                municipality_id=municipality_id
            ).order_by("name")
        else:
            context["administrative_posts"] = AdministrativePost.objects.none()

        if ap_id:
            context["sucos"] = Suco.objects.filter(
                administrative_post_id=ap_id
            ).order_by("name")
        else:
            context["sucos"] = Suco.objects.none()

        if suco_id:
            context["aldeias"] = Aldeia.objects.filter(
                suco_id=suco_id
            ).order_by("name")
        else:
            context["aldeias"] = Aldeia.objects.none()

        base_qs = self.get_queryset()

        context["report_by_municipality"] = (
            base_qs.values("parent__municipality__name")
            .annotate(total=Count("id"))
            .order_by("parent__municipality__name")
        )

        context["report_by_ap"] = (
            base_qs.values(
                "parent__administrative_post__name",
                "parent__municipality__name"
            )
            .annotate(total=Count("id"))
            .order_by("parent__municipality__name", "parent__administrative_post__name")
        )

        context["report_by_suco"] = (
            base_qs.values(
                "parent__suco__name",
                "parent__administrative_post__name"
            )
            .annotate(total=Count("id"))
            .order_by("parent__administrative_post__name", "parent__suco__name")
        )

        context["report_by_aldeia"] = (
            base_qs.values(
                "parent__aldeia__name",
                "parent__suco__name"
            )
            .annotate(total=Count("id"))
            .order_by("parent__suco__name", "parent__aldeia__name")
        )

        return context


class ClassAssociationReportView(TemplateView):
    template_name = "dashboards/class_association_report.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("core:login")
        if request.user.role != "moe_admin":
            messages.error(request, "Ita la iha permisaun atu haree relatoriu ida ne'e.")
            return redirect("core:moe_admin_dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        preschool_id = self.request.GET.get("preschool", "")
        start_date_value = self.request.GET.get("start_date", "")
        end_date_value = self.request.GET.get("end_date", "")
        start_date = parse_date(start_date_value) if start_date_value else None
        end_date = parse_date(end_date_value) if end_date_value else None

        enrollments = (
            ClassroomChild.objects
            .select_related("classroom", "classroom__preschool", "child", "child__parent")
            .order_by("-enrolled_at", "classroom__preschool__name", "classroom__name")
        )

        if preschool_id:
            enrollments = enrollments.filter(classroom__preschool_id=preschool_id)
        if start_date:
            enrollments = enrollments.filter(enrolled_at__date__gte=start_date)
        if end_date:
            enrollments = enrollments.filter(enrolled_at__date__lte=end_date)

        context.update({
            "preschools": Preschool.objects.all().order_by("name"),
            "selected_preschool": preschool_id,
            "start_date": start_date_value,
            "end_date": end_date_value,
            "total_child_additions": enrollments.count(),
            "total_parent_additions": enrollments.values("child__parent_id").distinct().count(),
            "total_preschools": enrollments.values("classroom__preschool_id").distinct().count(),
            "total_classes": enrollments.values("classroom_id").distinct().count(),
            "classroom_summary": (
                enrollments
                .values(
                    "classroom__preschool__name",
                    "classroom__name",
                    "classroom__group",
                )
                .annotate(
                    child_total=Count("id"),
                    parent_total=Count("child__parent_id", distinct=True),
                    first_added=Min("enrolled_at"),
                    last_added=Max("enrolled_at"),
                )
                .order_by("classroom__preschool__name", "classroom__name")
            ),
            "daily_summary": (
                enrollments
                .annotate(day=TruncDate("enrolled_at"))
                .values("day", "classroom__preschool__name")
                .annotate(
                    child_total=Count("id"),
                    parent_total=Count("child__parent_id", distinct=True),
                )
                .order_by("-day", "classroom__preschool__name")
            ),
            "enrollments": enrollments,
        })
        return context
