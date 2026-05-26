from django.urls import path

from .views import (
    EquipmentCreateView,
    EquipmentListView,
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
        'ajax/load-classrooms/',
        load_classrooms,
        name='ajax-load-classrooms'
    ),
]
