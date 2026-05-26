from django.contrib import admin

# Register your models here.
from .models import SupportTicket, SupportCategory

from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import SupportTicket

User = get_user_model()


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):

    list_display = (
        'ticket_number',
        'teacher',
        'preschool',
        'status',
        'created_at',
    )

    list_filter = (
        'status',
        'created_at',
    )

    # Search only teacher fields
    search_fields = (
        'teacher__first_name',
        'teacher__last_name',
        'teacher__username',
    )

    ordering = (
        '-created_at',
    )

    readonly_fields = (
        'ticket_number',
        'created_at',
    )

    # Filter teacher dropdown to only users with teacher role
    def formfield_for_foreignkey(self, db_field, request, **kwargs):

        if db_field.name == "teacher":

            # OPTION 1:
            # If your User model has role field
            kwargs["queryset"] = User.objects.filter(
                role='teacher'
            )

            # OPTION 2:
            # If using Django Groups instead of role field
            # kwargs["queryset"] = User.objects.filter(
            #     groups__name='Teacher'
            # )

        return super().formfield_for_foreignkey(
            db_field,
            request,
            **kwargs
        )
@admin.register(SupportCategory)
class SupportCategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title',)      

