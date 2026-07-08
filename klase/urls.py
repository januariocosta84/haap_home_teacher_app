from django.urls import path

from .views import (
    AddChildToClassroomView,
    AjaxRegisterChild,
    ClassroomDetailView,
    ClassroomListView,
    DownloadClassroomChildrenView,
    RemoveStudentFromClassroomView,
    SchoolClassroomListView,
    TeacherDashboardView,
    TeacherProDashboardView,
    TeacherSchoolListView,
)

app_name = 'klase'

urlpatterns = [

    # ── Teacher views ─────────────────────────────────────────
    path('teacher/schools/',                         TeacherSchoolListView.as_view(),    name='teacher_school_list'),
    path('teacher/school/<uuid:preschool_id>/classrooms/', SchoolClassroomListView.as_view(), name='school_classroom_list'),

    # ── Classroom CRUD ────────────────────────────────────────
    path('classrooms/',                                     ClassroomListView.as_view(),               name='classroom_list'),
    path('classroom/<uuid:classroom_id>/',                  ClassroomDetailView.as_view(),             name='classroom_detail'),
    path('classroom/<uuid:classroom_id>/add-child/',        AddChildToClassroomView.as_view(),         name='classroom_child_add'),
    path('classroom/<uuid:classroom_id>/remove-child/<uuid:enrollment_id>/', RemoveStudentFromClassroomView.as_view(), name='classroom_child_remove'),
    path('classroom/<uuid:classroom_id>/children/download/', DownloadClassroomChildrenView.as_view(), name='classroom_children_download'),

    # ── Legacy / Dashboard ────────────────────────────────────
    path('teacher/dashboard/',      TeacherDashboardView.as_view(),    name='teacher_dashboard'),
    path('teacher/dashboard/pro/',  TeacherProDashboardView.as_view(), name='teacher_dashboard_pro'),

    # ── AJAX ──────────────────────────────────────────────────
    path('ajax/register-child/', AjaxRegisterChild.as_view(), name='ajax_child_register'),
]
