from django.urls import path

from preschools import views
from .views import (
    ClassroomCreateView,
    ClassroomDetailView,
    ClassroomUpdateView,
    PreschoolCreateView,
    PreschoolDeleteView,
    PreschoolDetailView,
    PreschoolListView,
    PreschoolUpdateView,
    TeacherPreschoolListView,
    join_view,
)

app_name = 'preschools'

urlpatterns = [

    # ── Preschool CRUD ────────────────────────────────────────
    path('',               PreschoolListView.as_view(),   name='preschool_list'),
    path('create/',        PreschoolCreateView.as_view(), name='preschool_create'),
    path('<uuid:pk>/',     PreschoolDetailView.as_view(), name='preschool_detail'),
    path('<uuid:pk>/edit/',   PreschoolUpdateView.as_view(), name='preschool_update'),
    path('<uuid:pk>/delete/', PreschoolDeleteView.as_view(), name='preschool_delete'),

    # ── Teacher preschool claim list ──────────────────────────
    path('my-preschools/', TeacherPreschoolListView.as_view(), name='teacher_preschool_list'),
    path('join/<uuid:preschool_id>/', join_view, name='preschool_join'),

    # ── Teacher requests ──────────────────────────────────────
    path('teacher-requests/', views.PreschoolTeacherRequestListView.as_view(), name='teacher_request_list'),
    path('teacher-requests/<uuid:request_id>/approve/', views.approve_preschool_teacher_request, name='teacher_request_approve'),

    # ── Classroom (preschool-scoped) ──────────────────────────
    path('<uuid:id>/classroom/create/',   ClassroomCreateView.as_view(),  name='classroom_create'),
    path('classroom/<uuid:id>/',          ClassroomDetailView.as_view(),  name='classroom_detail'),
    path('classroom/<uuid:id>/edit/',     ClassroomUpdateView.as_view(),  name='classroom_update'),
    path('classroom/<uuid:id>/enroll/',   views.enroll_child,             name='classroom_enroll'),
]
