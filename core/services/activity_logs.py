from django.views.generic import ListView
from core.models import ActivityResult
from core.services.activity_filters import filter_by_role

class AppUsageLogListView(ListView):
    model = ActivityResult
    template_name = "dashboards/logs.html"
    paginate_by = 10
    context_object_name = "logs"

    def get_queryset(self):
        qs = ActivityResult.objects.select_related(
            "student", "student__parent"
        ).order_by("-created_at")

        activity = self.request.GET.get("activity")
        if activity:
            qs = qs.filter(activity_name__icontains=activity)

        return filter_by_role(qs, self.request.user)
