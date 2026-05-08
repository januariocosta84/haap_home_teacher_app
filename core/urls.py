from django.urls import path
from core.api_view import ActivityResultCreateAPIView, LoginAPIView, LogoutAPIView
from core.views import *


from core.views.activity_logs import ChildActivityView
from core.views.analytics_api import trend_data_api, summary_stats_api, get_municipalities_api
from core.views.send import send_whatsapp
from core.views.user_management import forgot_password, reset_password, verify_otp

app_name = "core"

urlpatterns = [
    path("login/", user_login, name="login"),
    path("logout/", user_logout, name="logout"),

    path("children/", children_list, name="children_list"),
    path("children/add/", child_registration, name="child_add"),

    path("dashboard/moe/", moe_admin_dashboard, name="moe_admin_dashboard"),

    # User management (MoE admin)
    path("dashboard/users/", UserManagementView.as_view(), name="user_management"),
    path("dashboard/users/<uuid:user_id>/view/", view_user, name="view_user"),
    path("dashboard/users/<uuid:user_id>/edit/", edit_user, name="edit_user"),
    path("dashboard/users/<uuid:user_id>/delete/", delete_user, name="delete_user"),
    path("dashboard/register/user/", register_user, name="register_user"),

    path("dashboard/logs/", AppUsageLogListView, name="logs"),
   # path("reports/activities/", ActivityReportView.as_view(), name="activity_report"),

    path("export/parents/", export_parents_pdf, name="export_parents_pdf"),

    # Public parent registration
    path("register/parent/", ParentRegisterView.as_view(), name="parent_register"),
    path("dashboard/profile/", profile_view, name="profile"),
    path("dashboard/profile/update-image/", update_profile_image, name="update_profile_image"),
    path("dashboard/profile/change-password/", change_password, name="change_password"),

    path('dashboard/municipality/', municipality_dashboard, name='municipality_dashboard'),
    path('dashboard/teacher/', teacher_dashboard, name='teacher_dashboard'),

    path('dashboard/apk/', apk_list, name='apk_list'),
    path('dashboard/apk/upload/', upload_apk, name='upload_apk'),
    path('dashboard/apk/<uuid:apk_id>/edit/', edit_apk, name='edit_apk'),

    path('check-whatsapp-number/', check_whatsapp_number, name='check_whatsapp_number'),
    path("ajax/load-administrative-posts/",load_administrative_posts, name="ajax_load_admin_posts"),
    path("ajax/load-sucos/", load_sucos, name="ajax_load_sucos"),
    path("ajax/load-aldeias/", load_aldeias, name="ajax_load_aldeias"),

     #APk
    path("dashboard/apk/latest/", apk_list, name="latest_apk"),
    
    # Child management
    path('dashboard/children/', children_list, name='children_list'), 
    path('dashboard/children/register/', child_registration, name='register_child'),
    path('dashboard/children/<uuid:child_id>/edit/', edit_child, name='edit_child'),
    path('dashboard/children/<uuid:child_id>/delete/', delete_child, name='delete_child'),

    #api
    path("api_login/", LoginAPIView.as_view(), name="api-login"),
    path("api_logout/", LogoutAPIView.as_view(), name="api-logout"),
    path("activity-results/", ActivityResultCreateAPIView.as_view(),name="activity-result-create"),

    #child details activity
    path("activity/<uuid:child_id>/", ChildActivityView.as_view(), name="child-activity"),

    path('api/trends/', trend_data_api, name='api_trends'),
    path('api/summary/', summary_stats_api, name='api_summary'),
    path('api/municipalities/', get_municipalities_api, name='api_municipalities'),

    #reset password
    path('forgot-password/', forgot_password, name='forgot_password'),
    path('verify-otp/', verify_otp, name='verify_otp'),
    path('reset-password/', reset_password, name='reset_password'),

    path('send-whatsapp/', send_whatsapp, name='send_whatsapp'),
]