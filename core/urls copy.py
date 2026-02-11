# core/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('parent/', views.parent, name='parent_dashboard'),

    # Child management
    path('dashboard/children/', views.children_list, name='children_list'), 
    path('dashboard/children/register/', views. child_registration, name='register_child'),
    path('dashboard/children/<uuid:child_id>/edit/', views.edit_child, name='edit_child'),
    path('dashboard/children/<uuid:child_id>/delete/', views.delete_child, name='delete_child'),

    # School management
    path('dashboard/municipality/', views.municipality_dashboard, name='municipality_dashboard'),
    path('dashboard/teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    
    # APK management
    path('dashboard/apk/', views.apk_list, name='apk_list'),
    path('dashboard/apk/upload/', views.upload_apk, name='upload_apk'),
    path('dashboard/apk/<uuid:apk_id>/edit/', views.edit_apk, name='edit_apk'),
    

    # User profile image update
    path('dashboard/profile/image/update/', views.update_profile_image, name='update_profile_image'),
     path("dashboard/profile/", views.profile_view, name="profile"),
       
    #path('register/parent/', views.parent_register, name='parent_register'),
    path('check-whatsapp-number/', views.check_whatsapp_number, name='check_whatsapp_number'),
    path("register/parent/", views.ParentRegisterView.as_view(), name="parent_register"),
    path('admin/', views.admin_parent_child_list, name='admin'),
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    path("dashboard/admin/", views.moe_admin_dashboard, name="moe_admin_dashboard"),
    path("dashboard/users/", views.UserManagementView.as_view(), name="user_management"),
    path("dashboard/users/<uuid:user_id>/view/", views.view_user, name="view_user"),
    path("dashboard/users/<uuid:user_id>/edit/", views.edit_user, name="edit_user"),
    path("dashboard/users/<uuid:user_id>/delete/", views.delete_user, name="delete_user"),
    path('dashboard/parents/', views.parent_list, name='parent_list'),
        path('dashboard/parents/export-pdf/', views.export_parents_pdf, name='export_parents_pdf'),
    path('dashboard/logs/', views.AppUsageLogListView.as_view(), name='app_usage_logs'),
    path('reports/children/', views.ChildrenReportView.as_view(), name='children_report'),
    #path('reports/apk/', views.APKReportView.as_view(), name='apk_report'),
      # AJAX endpoints
    path("ajax/load-administrative-posts/", views.LoadAdministrativePosts.as_view(), name="ajax_load_admin_posts"),
    path("ajax/load-sucos/", views.LoadSucos.as_view(), name="ajax_load_sucos"),
    path("ajax/load-aldeias/", views.LoadAldeias.as_view(), name="ajax_load_aldeias"),
    path("dashboard/register/user/", views.register_user, name="register_user"),


    #APk
    path("dashboard/apk/latest/", views.LatestApkView.as_view(), name="latest_apk"),
        # Password reset URLs
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(template_name="registration/password_reset_form.html"),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(template_name="registration/password_reset_confirm.html"),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html"),
        name="password_reset_complete",
    ),
]