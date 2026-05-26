from django.urls import path
from preschools import views


from .views import (
    ClassroomCreateView,
    ClassroomDetailView,
    ClassroomUpdateView,
    PreschoolDetailView,
    PreschoolListView,
    PreschoolCreateView,
    PreschoolUpdateView,
    PreschoolDeleteView,
    TeacherPreschoolListView,
    join_view
)

app_name = 'preschools'

urlpatterns = [
    path('list/', PreschoolListView.as_view(), name='preschool_list'),
    path('list_claim/', TeacherPreschoolListView.as_view(), name='preschool_list_claim'),
    path('detail/<uuid:pk>/', PreschoolDetailView.as_view(), name='preschool_detail'),
    path('create/', PreschoolCreateView.as_view(), name='preschool_create'),
    path('edit/<uuid:pk>/', PreschoolUpdateView.as_view(), name='preschool_edit'),
    path('delete/<uuid:pk>/', PreschoolDeleteView.as_view(), name='preschool_delete'),
    # Change <uuid:preschool_id> to <uuid:id>
    path('join/<uuid:preschool_id>/', views.join_view, name='join_preschool'),
    path('teacher-requests/', views.PreschoolTeacherRequestListView.as_view(), name='preschool_teacher_requests'),
    path('teacher-requests/<uuid:request_id>/approve/', views.approve_preschool_teacher_request, name='approve_preschool_teacher_request'),
    path("list-preschool/<uuid:id>/", PreschoolDetailView.as_view(), name="preschool_detail"),

    path(
        "preschool/<uuid:id>/classroom/add/",
        ClassroomCreateView.as_view(),
        name="add_classroom"
    ),

    path(
        "classroom/<uuid:id>/",
        ClassroomDetailView.as_view(),
        name="classroom_detail"
    ),

    path(
        "classroom/<uuid:id>/enroll/",
        views.enroll_child,
        name="enroll_child"
    ),

    path(
        "classroom/<uuid:id>/edit/",
        ClassroomUpdateView.as_view(),
        name="edit_classroom"
    ),
]