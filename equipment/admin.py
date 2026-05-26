from django.contrib import admin
from .models import Equipment, EquipmentHistory


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = (
        'serial_number',
        'equipment_type',
        'model_number',
        'preschool',
        'classroom',
        'teacher',
        'created_at',
    )

    list_filter = (
        'equipment_type',
        'preschool',
        'created_at',
    )

    search_fields = (
        'serial_number',
        'model_number',
    )


@admin.register(EquipmentHistory)
class EquipmentHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'equipment',
        'old_preschool',
        'new_preschool',
        'changed_at',
    )

    list_filter = (
        'changed_at',
    )