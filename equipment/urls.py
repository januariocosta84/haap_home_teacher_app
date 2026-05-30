from django.urls import path

from .views import (
    EquipmentCreateView,
    EquipmentListView,
    EquipmentDetailView,
    EquipmentUpdateView,
    EquipmentAssignmentChangeView,
    EquipmentDeleteView,
    EquipmentByPreschoolView,
    EquipmentByClassroomView,
    EquipmentByTeacherView,
    load_classrooms,
)

urlpatterns = [

    path(
        'add/',
        EquipmentCreateView.as_view(),
        name='equipment-add'
    ),

    path(
        'list/',
        EquipmentListView.as_view(),
        name='equipment-list'
    ),

    path(
        '<uuid:pk>/',
        EquipmentDetailView.as_view(),
        name='equipment-detail'
    ),

    path(
        '<uuid:pk>/edit/',
        EquipmentUpdateView.as_view(),
        name='equipment-update'
    ),

    path(
        '<uuid:pk>/assignment/',
        EquipmentAssignmentChangeView.as_view(),
        name='equipment-assignment-change'
    ),

    path(
        '<uuid:pk>/delete/',
        EquipmentDeleteView.as_view(),
        name='equipment-delete'
    ),

    path(
        'preschool/<uuid:preschool_id>/',
        EquipmentByPreschoolView.as_view(),
        name='equipment-by-preschool'
    ),

    path(
        'classroom/<uuid:classroom_id>/',
        EquipmentByClassroomView.as_view(),
        name='equipment-by-classroom'
    ),

    path(
        'teacher/<uuid:teacher_id>/',
        EquipmentByTeacherView.as_view(),
        name='equipment-by-teacher'
    ),

    path(
        'ajax/load-classrooms/',
        load_classrooms,
        name='ajax-load-classrooms'
    ),
]
