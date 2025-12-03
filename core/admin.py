from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Municipality, AdministrativePost, Suco, Aldeia,
    Child, AppUsageLog, PreschoolEnrollmentOptIn,
    ApkVersion, WhatsAppMessage, ActivityResult
)

# ------------------------------
# Location Models
# ------------------------------
@admin.register(Municipality)
class MunicipalityAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(AdministrativePost)
class AdministrativePostAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "municipality")
    list_filter = ("municipality",)
    search_fields = ("name", "municipality__name")


@admin.register(Suco)
class SucoAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "administrative_post")
    list_filter = ("administrative_post__municipality", "administrative_post")
    search_fields = ("name", "administrative_post__name", "administrative_post__municipality__name")


@admin.register(Aldeia)
class AldeiaAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "suco")
    list_filter = ("suco__administrative_post__municipality", "suco__administrative_post", "suco")
    search_fields = ("name", "suco__name", "suco__administrative_post__name")


# ------------------------------
# Custom User Admin
# ------------------------------
class UserAdmin(BaseUserAdmin):
    model = User
    list_display = (
        "id", "username", "first_name", "last_name", "role", "whatsapp_number",
        "municipality", "administrative_post", "suco", "aldeia", "is_verified"
    )
    list_filter = ("role", "municipality", "administrative_post", "suco", "aldeia", "is_verified")
    search_fields = ("username", "first_name", "last_name", "whatsapp_number", "email")
    ordering = ("created_at",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "email", "whatsapp_number", "address")}),
        ("Role & Verification", {"fields": ("role", "is_verified", "temp_password")}),
        ("Location", {"fields": ("municipality", "administrative_post", "suco", "aldeia")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )


admin.site.register(User, UserAdmin)


# ------------------------------
# Other Models
# ------------------------------
@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "parent", "year_of_birth", "age_group")
    list_filter = ("age_group", "parent__municipality")
    search_fields = ("first_name", "parent__first_name", "parent__last_name")


@admin.register(AppUsageLog)
class AppUsageLogAdmin(admin.ModelAdmin):
    list_display = ("id", "child", "theme", "activity_type", "date_accessed", "was_successful")
    list_filter = ("activity_type", "is_assessed", "was_successful", "date_accessed")
    search_fields = ("child__first_name", "theme")


@admin.register(PreschoolEnrollmentOptIn)
class PreschoolEnrollmentOptInAdmin(admin.ModelAdmin):
    list_display = ("id", "parent", "contact_method", "created_at")
    list_filter = ("contact_method",)
    search_fields = ("parent__first_name", "parent__last_name", "parent__whatsapp_number")


@admin.register(ApkVersion)
class ApkVersionAdmin(admin.ModelAdmin):
    list_display = ("id", "version_name", "is_latest", "released_at")
    list_filter = ("is_latest",)
    search_fields = ("version_name",)


@admin.register(WhatsAppMessage)
class WhatsAppMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "to_number", "template_type", "status", "sent_at")
    list_filter = ("template_type", "status", "sent_at")
    search_fields = ("to_number", "template_type")


@admin.register(ActivityResult)
class ActivityResultAdmin(admin.ModelAdmin):
    list_display = ("id", "parent", "student", "activity_name", "activity_result", "created_at")
    list_filter = ("activity_name", "created_at", "parent", "student")
    search_fields = ("activity_name", "parent__first_name", "parent__last_name", "student__first_name")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("parent", "student")}),
        ("Categories", {"fields": ("category1", "category2", "category3")}),
        ("Activity", {"fields": ("activity_name", "activity_result")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
