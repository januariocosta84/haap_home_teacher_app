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
    EquipmentTypeListView,
    EquipmentTypeCreateView,
    EquipmentTypeUpdateView,
    EquipmentTypeDeleteView,
    equipment_type_info,
    load_classrooms,
    export_preschool_equipment_excel,
    export_preschool_equipment_pdf,
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
    path('by-preschool/<uuid:preschool_id>/',              EquipmentByPreschoolView.as_view(),     name='equipment_by_preschool'),
    path('by-preschool/<uuid:preschool_id>/export/excel/', export_preschool_equipment_excel,       name='equipment_preschool_export_excel'),
    path('by-preschool/<uuid:preschool_id>/export/pdf/',   export_preschool_equipment_pdf,         name='equipment_preschool_export_pdf'),
    path('by-classroom/<uuid:classroom_id>/',              EquipmentByClassroomView.as_view(),     name='equipment_by_classroom'),
    path('by-teacher/<uuid:teacher_id>/',                  EquipmentByTeacherView.as_view(),       name='equipment_by_teacher'),

    # ── Equipment Type management ─────────────────────────────
    path('types/',                EquipmentTypeListView.as_view(),   name='equipment_type_list'),
    path('types/create/',         EquipmentTypeCreateView.as_view(), name='equipment_type_create'),
    path('types/<int:pk>/edit/',  EquipmentTypeUpdateView.as_view(), name='equipment_type_update'),
    path('types/<int:pk>/delete/',EquipmentTypeDeleteView.as_view(), name='equipment_type_delete'),

    # ── AJAX ──────────────────────────────────────────────────
    path('ajax/load-classrooms/', load_classrooms, name='ajax_load_classrooms'),
    path('ajax/type-info/',       equipment_type_info, name='ajax_equipment_type_info'),
]
