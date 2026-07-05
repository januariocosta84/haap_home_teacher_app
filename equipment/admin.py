from django.contrib import admin
from .models import Equipment, EquipmentAssignmentHistory


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = (
        'serial_number',
        'equipment_type',
        'model_number',
        'status',
        'preschool',
        'classroom',
        'teacher',
        'created_at',
    )

    list_filter = (
        'equipment_type',
        'status',
        'preschool',
        'created_at',
    )

    search_fields = (
        'serial_number',
        'model_number',
    )


@admin.register(EquipmentAssignmentHistory)
class EquipmentAssignmentHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'equipment',
        'old_preschool',
        'new_preschool',
        'changed_by',
        'changed_at',
    )

    list_filter = (
        'changed_at',
    )

    readonly_fields = (
        'equipment',
        'old_preschool',
        'old_classroom',
        'old_teacher',
        'new_preschool',
        'new_classroom',
        'new_teacher',
        'changed_by',
        'changed_at',
    )