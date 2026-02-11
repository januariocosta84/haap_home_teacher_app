from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from core.models import User, Child

@login_required
def moe_admin_dashboard(request):
    context = {
        "all_users": User.objects.count(),
        "parents": User.objects.filter(role="parent").count(),
        "municipality_analysts": User.objects.filter(role="municipality_analyst").count(),
        "children": Child.objects.count(),
        "teachers": User.objects.filter(role="teacher").count(),
        "all_parents": User.objects.filter(role="parent"),
        "all_children": Child.objects.all(),
        "all_teachers": User.objects.filter(role="teacher"),
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
