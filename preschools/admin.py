from django.contrib import admin

# Register your models here.
from .models import Preschool, PreschoolTeacher

@admin.register(Preschool)
class PreschoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'preschool_type', 'municipality', 'administrative_post', 'suco', 'aldeia')
    search_fields = ('name',)
    list_filter = ('preschool_type', 'municipality')
    
# @admin.register(PreschoolTeacher)
# class PreschoolTeacherAdmin(admin.ModelAdmin):
#     list_display = ('preschool', 'teacher', 'is_primary', 'assigned_at', 'is_active')
#     search_fields = ('preschool__name', 'teacher__username')
#     list_filter = ('preschool',)
