from django.urls import path

from core.api_view import ActivityResultCreateAPIView, LoginAPIView, LogoutAPIView
from core.views import *
from core.views.activity_logs import ChildActivityView, TeacherActivityLogListView
from core.views.analytics_api import get_municipalities_api, summary_stats_api, trend_data_api
from core.views.apk import (
    apk_notif_count, apk_notif_list,
    apk_notif_mark_all_read, apk_notif_mark_read,
    delete_apk,
)
from core.views.audit import audit_detail, audit_export, audit_list
from core.views.auditing_portal import (
    auditing_dashboard, auditing_export,
    auditing_log_detail, auditing_login, auditing_logout, auditing_logs,
)
from core.views.parents import verify_register_otp
from core.views.send import send_whatsapp
from core.views.user_management import forgot_password, reset_password, verify_otp

app_name = 'core'

urlpatterns = [

    # ── Authentication ────────────────────────────────────────
    path('login/',   user_login,  name='login'),
    path('logout/',  user_logout, name='logout'),

    # ── Public Registration ───────────────────────────────────
    path('register/parent/',      ParentRegisterView.as_view(), name='parent_register'),
    path('register/teacher/',     TeacherRegisterView.as_view(), name='teacher_register'),
    path('verify-register-otp/',  verify_register_otp, name='register_otp_verify'),

    # ── Password Reset ────────────────────────────────────────
    path('forgot-password/', forgot_password, name='password_forgot'),
    path('verify-otp/',      verify_otp,      name='password_otp_verify'),
    path('reset-password/',  reset_password,  name='password_reset'),

    # ── Dashboards ────────────────────────────────────────────
    path('dashboard/moe/',          moe_admin_dashboard,   name='moe_admin_dashboard'),
    path('dashboard/municipality/', municipality_dashboard, name='municipality_dashboard'),

    # ── Profile ───────────────────────────────────────────────
    path('dashboard/profile/',                  profile_view,          name='profile'),
    path('dashboard/profile/update-image/',     update_profile_image,  name='profile_image_update'),
    path('dashboard/profile/change-password/',  change_password,       name='password_change'),

    # ── User Management ───────────────────────────────────────
    path('dashboard/users/',                         UserManagementView.as_view(), name='user_list'),
    path('dashboard/users/<uuid:user_id>/view/',     view_user,        name='user_detail'),
    path('dashboard/users/<uuid:user_id>/approve/',  approve_teacher,  name='user_approve'),
    path('dashboard/users/<uuid:user_id>/edit/',     edit_user,        name='user_update'),
    path('dashboard/users/<uuid:user_id>/delete/',   delete_user,      name='user_delete'),
    path('dashboard/users/register/',                register_user,    name='user_create'),

    # ── Children ──────────────────────────────────────────────
    path('dashboard/children/',                     children_list,     name='child_list'),
    path('dashboard/children/register/',            child_registration, name='child_create'),
    path('dashboard/children/<uuid:child_id>/edit/',   edit_child,     name='child_update'),
    path('dashboard/children/<uuid:child_id>/delete/', delete_child,   name='child_delete'),

    # ── APK ───────────────────────────────────────────────────
    path('dashboard/apk/',                      apk_list,    name='apk_list'),
    path('dashboard/apk/upload/',               upload_apk,  name='apk_create'),
    path('dashboard/apk/<uuid:apk_id>/edit/',   edit_apk,    name='apk_update'),
    path('dashboard/apk/<uuid:apk_id>/delete/', delete_apk,  name='apk_delete'),
    path('dashboard/apk/<uuid:apk_id>/download/', download_apk, name='apk_download'),

    # ── Reports ───────────────────────────────────────────────
    path('dashboard/logs/',         AppUsageLogListView,           name='log_list'),
    path('dashboard/teacher-logs/', TeacherActivityLogListView.as_view(), name='teacher_log_list'),
    path('dashboard/reports/class-associations/', ClassAssociationReportView.as_view(), name='report_class_association'),
    path('export/parents/',         export_parents_pdf, name='export_parent_pdf'),

    # ── Audit Log (moe_admin only) ────────────────────────────
    path('dashboard/audit/',                          audit_list,   name='audit_list'),
    path('dashboard/audit/<uuid:log_id>/detail/',     audit_detail, name='audit_detail'),
    path('dashboard/audit/export/',                   audit_export, name='audit_export'),

    # ── Auditing Portal (moe_auditing role) ──────────────────
    path('auditing/login/',                           auditing_login,      name='auditing_login'),
    path('auditing/logout/',                          auditing_logout,     name='auditing_logout'),
    path('auditing/',                                 auditing_dashboard,  name='auditing_dashboard'),
    path('auditing/logs/',                            auditing_logs,       name='auditing_log_list'),
    path('auditing/<uuid:log_id>/detail/',            auditing_log_detail, name='auditing_log_detail'),
    path('auditing/export/',                          auditing_export,     name='auditing_export'),

    # ── APK Notifications ─────────────────────────────────────
    path('apk-notifications/count/',                  apk_notif_count,        name='apk_notif_count'),
    path('apk-notifications/',                        apk_notif_list,         name='apk_notif_list'),
    path('apk-notifications/<uuid:notif_id>/read/',   apk_notif_mark_read,    name='apk_notif_mark_read'),
    path('apk-notifications/read-all/',               apk_notif_mark_all_read, name='apk_notif_mark_all_read'),

    # ── AJAX / Cascading Dropdowns ────────────────────────────
    path('check-whatsapp/',                    check_whatsapp_number,      name='check_whatsapp'),
    path('ajax/load-administrative-posts/',    load_administrative_posts,  name='ajax_load_admin_posts'),
    path('ajax/load-sucos/',                   load_sucos,                 name='ajax_load_sucos'),
    path('ajax/load-aldeias/',                 load_aldeias,               name='ajax_load_aldeias'),

    # ── REST API ──────────────────────────────────────────────
    path('api/login/',             LoginAPIView.as_view(),              name='api_login'),
    path('api/logout/',            LogoutAPIView.as_view(),             name='api_logout'),
    path('api/activity-results/',  ActivityResultCreateAPIView.as_view(), name='api_activity_create'),
    path('api/activity/<uuid:child_id>/', ChildActivityView.as_view(), name='api_child_activity'),
    path('api/trends/',            trend_data_api,                     name='api_trends'),
    path('api/summary/',           summary_stats_api,                  name='api_summary'),
    path('api/municipalities/',    get_municipalities_api,             name='api_municipalities'),

    # ── Utility ───────────────────────────────────────────────
    path('send-whatsapp/', send_whatsapp, name='send_whatsapp'),
]
