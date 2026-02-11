from django.views.generic import ListView
from django.db.models import Count
from core.models import Child, Municipality, AdministrativePost, Suco, Aldeia

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
