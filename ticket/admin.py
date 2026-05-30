from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import SupportTicket, SupportTicketItem, SupportCategory

User = get_user_model()


class SupportTicketItemInline(admin.TabularInline):
    model = SupportTicketItem
    fields = ('item_type', 'details', 'preferred_format', 'app_features_to_learn')
    extra = 1


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):

    list_display = (
        'ticket_number',
        'teacher',
        'preschool',
        'status',
        'priority',
        'is_equipment_request',
        'is_training_request',
        'created_at',
    )

    list_filter = (
        'status',
        'priority',
        'is_equipment_request',
        'is_training_request',
        'created_at',
    )

    search_fields = (
        'teacher__first_name',
        'teacher__last_name',
        'teacher__username',
        'ticket_number',
    )

    ordering = (
        '-created_at',
    )

    readonly_fields = (
        'ticket_number',
        'created_at',
        'updated_at',
    )

    fieldsets = (
        ('Ticket Info', {
            'fields': ('ticket_number', 'status', 'priority')
        }),
        ('Teacher & Location', {
            'fields': ('teacher', 'preschool', 'classroom')
        }),
        ('Request Type', {
            'fields': ('is_equipment_request', 'is_training_request')
        }),
        ('Resolution', {
            'fields': ('resolution_note', 'resolved_at')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    inlines = [SupportTicketItemInline]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "teacher":
            kwargs["queryset"] = User.objects.filter(role='teacher')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(SupportTicketItem)
class SupportTicketItemAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'item_type', 'details_preview')
    list_filter = ('item_type', 'ticket__created_at')
    search_fields = ('ticket__ticket_number', 'details')
    readonly_fields = ('id',)

    def details_preview(self, obj):
        if obj.details:
            return obj.details[:50] + '...'
        return '-'
    details_preview.short_description = 'Details'


@admin.register(SupportCategory)
class SupportCategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title',)      

