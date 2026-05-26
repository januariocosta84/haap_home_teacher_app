from django.contrib import admin

from .models import Classroom, ClassroomChild

@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ('name', 'preschool')
    search_fields = ('name', 'preschool__name')
    list_filter = ('preschool',)

@admin.register(ClassroomChild)
class ClassroomChildAdmin(admin.ModelAdmin):
    list_display = ('classroom', 'child', 'enrolled_at', 'is_active')
    search_fields = ('classroom__name', 'child__first_name', 'child__last_name')
    list_filter = ('classroom', 'is_active')

    