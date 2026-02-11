from django.db.models import Q
from core.models import User


def filter_by_role(queryset, user):
    # ActivityResult stores parent as parent_whatsapp (string). Adapt filters accordingly.
    if user.role == "parent":
        return queryset.filter(parent_whatsapp=user.whatsapp_number)

    if user.role == "municipality_analyst":
        parent_whatsapps = User.objects.filter(municipality=user.municipality).values_list('whatsapp_number', flat=True)
        return queryset.filter(
            Q(parent_whatsapp__in=parent_whatsapps) |
            Q(student__parent__municipality=user.municipality)
        )

    if user.role == "teacher":
        return queryset.filter(
            student__parent__municipality=user.municipality
        )

    return queryset
