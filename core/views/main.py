from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

@login_required
def home(request):
    return render(request, 'core/home.html')


def parent_home(request):
    return render(request, 'core/parent_home.html')


def admin_parent_child_list(request):
    # Dummy dataset: 10 parents × 2 children = 20 children
    parents = []
    for i in range(1, 11):
        parent = {
            "username": f"parent{i}",
            "email": f"parent{i}@example.com",
            "children": [
                {"first_name": f"Child{i}A", "year_of_birth": 2020, "age_group": "Group A: 3-4 years"},
                {"first_name": f"Child{i}B", "year_of_birth": 2018, "age_group": "Group B: 5-6 years"},
            ],
        }
        parents.append(parent)

    # Flatten parent-child pairs for pagination
    parent_child_list = []
    for parent in parents:
        for child in parent["children"]:
            parent_child_list.append({
                "parent_username": parent["username"],
                "parent_email": parent["email"],
                "child_first_name": child["first_name"],
                "year_of_birth": child["year_of_birth"],
                "age_group": child["age_group"],
            })

    paginator = Paginator(parent_child_list, 5)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "core/parent_child_list.html", {"page_obj": page_obj})
