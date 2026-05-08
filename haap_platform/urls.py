from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

# ----------------------------
# Import views from modular files
# ----------------------------

from core.views.login_views import user_login, user_logout
from core.views.children import children_list, child_registration
from core.views.dashboards import moe_admin_dashboard, municipality_dashboard, teacher_dashboard
from core.views.activity_logs import AppUsageLogListView
from core.views.exports import export_parents_pdf
from core.views.parents import parents_list, add_parent, edit_parent, delete_parent
from core.views.user_management import user_list, add_user, edit_user, delete_user
from core.views.profile import profile_view
from core.views.apk import download_apk
from core.views.ajax_loads import get_children_by_parent, get_parents_by_municipality
# project/urls.py
handler404 = 'haap_app.core.views.custom_404'


# project/urls.py

# ----------------------------
# Root redirect based on user role
# ----------------------------
@login_required
def root_redirect(request):
    user = request.user
    if user.role == "moe_admin":
        return redirect("moe_admin_dashboard")
    elif user.role == "parent":
        return redirect("children_list")
    elif user.role == "teacher":
        return redirect("teacher_dashboard")
    elif user.role == "municipality_analyst":
        return redirect("municipality_dashboard")
    else:
        return redirect("login")  # fallback

# ----------------------------
# URL Patterns
# ----------------------------
handler404 = 'core.views.custom_404'  # ✅ must be here
urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # Root redirect
    path("", root_redirect, name="root_redirect"),

    # Include core app URLs (registers the 'core' namespace used by templates)
    path("", include(('core.urls', 'core'), namespace='core')),

    # Authentication
    path("login/", user_login, name="login"),
    path("logout/", user_logout, name="logout"),

    # Children
    path("children/", children_list, name="children_list"),
    path("children/add/", child_registration, name="child_add"),

    # Dashboards
    path("dashboard/moe/", moe_admin_dashboard, name="moe_admin_dashboard"),
    path("dashboard/municipality/", municipality_dashboard, name="municipality_dashboard"),
    path("dashboard/teacher/", teacher_dashboard, name="teacher_dashboard"),

    # Activity logs
  #  path("logs/", AppUsageLogListView.as_view(), name="logs"),

    # Exports
    path("export/parents/", export_parents_pdf, name="export_parents_pdf"),

    # Parents CRUD
    path("parents/", parents_list, name="parents_list"),
    path("parents/add/", add_parent, name="parent_add"),
    path("parents/edit/<int:parent_id>/", edit_parent, name="parent_edit"),
    path("parents/delete/<int:parent_id>/", delete_parent, name="parent_delete"),

    # Users CRUD
    path("users/", user_list, name="user_list"),
    path("users/add/", add_user, name="user_add"),
    path("users/edit/<int:user_id>/", edit_user, name="user_edit"),
    path("users/delete/<int:user_id>/", delete_user, name="user_delete"),
    
    # Profile
    path("profile/", profile_view, name="profile_view"),

    # APK downloads
    path("apk/download/<int:apk_id>/", download_apk, name="download_apk"),

    # AJAX endpoints
    path("ajax/children_by_parent/", get_children_by_parent, name="ajax_children_by_parent"),
    path("ajax/parents_by_municipality/", get_parents_by_municipality, name="ajax_parents_by_municipality"),

    path('dashboard/parents/', parents_list, name='parent_list'),

 

    
]

# ----------------------------
# Serve media files in development
# ----------------------------
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
