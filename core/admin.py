from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from core.models import Child, TeacherActivityLog

@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'age', 'parent')


@admin.register(TeacherActivityLog)
class TeacherActivityLogAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'preschool', 'activity_name', 'status', 'activity_date', 'created_at')
    list_filter = ('status', 'activity_date', 'preschool')
    search_fields = ('teacher__first_name', 'teacher__last_name', 'teacher__whatsapp_number', 'activity_name', 'theme', 'sub_theme')


