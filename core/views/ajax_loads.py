from django.http import JsonResponse
from core.models import Child, User, AdministrativePost, Suco, Aldeia

def get_children_by_parent(request):
    parent_id = request.GET.get('parent_id')
    children = []
    if parent_id:
        children_qs = Child.objects.filter(parent_id=parent_id)
        children = [{"id": c.id, "name": f"{c.first_name} {getattr(c, 'last_name', '')}"} for c in children_qs]
    return JsonResponse(children, safe=False)


def get_parents_by_municipality(request):
    municipality_id = request.GET.get('municipality_id')
    parents = []
    if municipality_id:
        parents_qs = User.objects.filter(role="parent", municipality_id=municipality_id)
        parents = [{"id": p.id, "name": f"{p.first_name} {getattr(p, 'last_name', '')}"} for p in parents_qs]
    return JsonResponse(parents, safe=False)


# AJAX: cascading dropdowns

def load_administrative_posts(request):
    municipality_id = request.GET.get("municipality_id")
    posts = AdministrativePost.objects.filter(municipality_id=municipality_id).values("id", "name")
    return JsonResponse(list(posts), safe=False)


def load_sucos(request):
    post_id = request.GET.get("administrative_post_id")
    sucos = Suco.objects.filter(administrative_post_id=post_id).values("id", "name")
    return JsonResponse(list(sucos), safe=False)


def load_aldeias(request):
    suco_id = request.GET.get("suco_id")
    aldeias = Aldeia.objects.filter(suco_id=suco_id).values("id", "name")
    return JsonResponse(list(aldeias), safe=False)
