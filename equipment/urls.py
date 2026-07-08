from django.urls import path

from .views import (
    EquipmentByClassroomView,
    EquipmentByPreschoolView,
    EquipmentByTeacherView,
    EquipmentAssignmentChangeView,
    EquipmentCreateView,
    EquipmentDeleteView,
    EquipmentDetailView,
    EquipmentListView,
    EquipmentUpdateView,
    load_classrooms,
)

app_name = 'equipment'

urlpatterns = [

    # ── Equipment CRUD ────────────────────────────────────────
    path('',                     EquipmentListView.as_view(),   name='equipment_list'),
    path('create/',              EquipmentCreateView.as_view(), name='equipment_create'),
    path('<uuid:pk>/',           EquipmentDetailView.as_view(), name='equipment_detail'),
    path('<uuid:pk>/edit/',      EquipmentUpdateView.as_view(), name='equipment_update'),
    path('<uuid:pk>/delete/',    EquipmentDeleteView.as_view(), name='equipment_delete'),
    path('<uuid:pk>/assignment/', EquipmentAssignmentChangeView.as_view(), name='equipment_assignment_update'),

    # ── Filtered lists ────────────────────────────────────────
    path('by-preschool/<uuid:preschool_id>/',   EquipmentByPreschoolView.as_view(),  name='equipment_by_preschool'),
    path('by-classroom/<uuid:classroom_id>/',   EquipmentByClassroomView.as_view(),  name='equipment_by_classroom'),
    path('by-teacher/<uuid:teacher_id>/',       EquipmentByTeacherView.as_view(),    name='equipment_by_teacher'),

    # ── AJAX ──────────────────────────────────────────────────
    path('ajax/load-classrooms/', load_classrooms, name='ajax_load_classrooms'),
]
