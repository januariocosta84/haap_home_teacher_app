# core/models.py

import os
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
# ---------------------------------
# 1. Municipality
# ---------------------------------
class Municipality(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'municipalities'
        ordering = ['name']

    def __str__(self):
        return self.name


# ---------------------------------
# 2. Administrative Post
# ---------------------------------
class AdministrativePost(models.Model):
    id = models.AutoField(primary_key=True)
    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE, related_name="administrative_posts")
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'administrative_posts'
        unique_together = ('municipality', 'name')
        ordering = ['municipality__name', 'name']

    def __str__(self):
        return f"{self.name}"


# ---------------------------------
# 3. Suco
# ---------------------------------
class Suco(models.Model):
    id = models.AutoField(primary_key=True)
    administrative_post = models.ForeignKey(AdministrativePost, on_delete=models.CASCADE, related_name="sucos")
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'sucos'
        unique_together = ('administrative_post', 'name')
        ordering = ['administrative_post__name', 'name']

    def __str__(self):
        return f"{self.name}"


# ---------------------------------
# 4. Aldeia
# ---------------------------------
class Aldeia(models.Model):
    id = models.AutoField(primary_key=True)
    suco = models.ForeignKey(Suco, on_delete=models.CASCADE, related_name="aldeias")
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'aldeias'
        unique_together = ('suco', 'name')
        ordering = ['suco__name', 'name']

    def __str__(self):
        return f"{self.name}"

# user profile image upload path
def user_image_upload_path(instance, filename):
    # Store uploads in "users/<user_id>/<filename>"
    ext = filename.split('.')[-1]
    filename = f"profile.{ext}"
    return os.path.join("users", str(instance.id), filename)

class User(AbstractUser):
    image = models.ImageField(
        upload_to=user_image_upload_path,
        default="defaults/user.png",   # <-- place a default image in MEDIA_ROOT/defaults/user.png
        blank=True,
        null=True
    )
    ROLE_CHOICES = [
        ('parent', 'Parent/Carer'),
        ('moe_admin', 'MoE Admin'),
        ('moe_auditing', 'MoE Auditing'),
        ('municipality_analyst', 'Municipality Analyst'),
        ('teacher', 'Teacher'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    whatsapp_number = models.CharField(max_length=15, unique=True)
    email = models.EmailField(blank=True, null=True)

    # New fields for parent registration
    first_name = models.CharField(max_length=50)  # already in AbstractUser
    last_name = models.CharField(max_length=50)   # already in AbstractUser
    address = models.CharField(max_length=255, blank=True, null=True)

    municipality = models.ForeignKey(Municipality, on_delete=models.SET_NULL, null=True, blank=True, related_name="users")
    administrative_post = models.ForeignKey(AdministrativePost, on_delete=models.SET_NULL, null=True, blank=True, related_name="users")
    suco = models.ForeignKey(Suco, on_delete=models.SET_NULL, null=True, blank=True, related_name="users")
    aldeia = models.ForeignKey(Aldeia, on_delete=models.SET_NULL, null=True, blank=True, related_name="users")

    is_verified = models.BooleanField(default=False)
    temp_password = models.CharField(max_length=128, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'whatsapp_number'
    REQUIRED_FIELDS = ['username', 'role']

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['whatsapp_number']),
            models.Index(fields=['role', 'municipality']),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"
    
# ---------------------------------
# 2. Location Hierarchy
# ---------------------------------
class Location(models.Model):
    TYPE_CHOICES = [
        ('municipality', 'Municipality'),
        ('town', 'Town'),
        ('village', 'Village'),
    ]

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )

    class Meta:
        db_table = 'locations'
        indexes = [
            models.Index(fields=['type']),
            models.Index(fields=['parent']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


# ---------------------------------
# 3. Child Profile
# ---------------------------------
class Child(models.Model):
    AGE_GROUP_CHOICES = [
        ('A', 'Grupo A: Tinan 3-4 '),
        ('B', 'Grupo B: Tinan 5-6 '),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='children')
    first_name = models.CharField(max_length=50)
    year_of_birth = models.PositiveSmallIntegerField()
    age_group = models.CharField(max_length=1, choices=AGE_GROUP_CHOICES)

    # Auto-generated login ID (like a student code)
    user_id = models.CharField(max_length=30, unique=True, editable=False, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'children'
        indexes = [
            models.Index(fields=['parent']),
            models.Index(fields=['age_group']),
            models.Index(fields=['user_id']),
        ]

    def save(self, *args, **kwargs):
        if not self.user_id:
            # Example format: CH-XXXXXX (unique code)
            self.user_id = f"{self.first_name[:3].upper()}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} ({self.get_age_group_display()}) | {self.user_id}"
    @property
    def age(self):
        import datetime
        current_year = datetime.date.today().year
        return current_year - self.year_of_birth
# ---------------------------------
# 4. App Usage Logs
# ---------------------------------
class AppUsageLog(models.Model):
    ACTIVITY_TYPE_CHOICES = [
        ('Numero', 'Numbers'),
        ('Lian', 'Language'),
        ('Arte', 'Art'),
        ('Motri', 'Motor Skills'),
        ('Sosyal', 'Social Skills'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='usage_logs')
    theme = models.CharField(max_length=50)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPE_CHOICES)
    group = models.CharField(max_length=1, choices=Child.AGE_GROUP_CHOICES)
    is_assessed = models.BooleanField(default=False)
    was_successful = models.BooleanField(default=False)
    date_accessed = models.DateField()
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = 'app_usage_logs'
        indexes = [
            models.Index(fields=['child', 'date_accessed']),
            models.Index(fields=['theme']),
            models.Index(fields=['activity_type']),
            models.Index(fields=['date_accessed']),
            models.Index(fields=['is_assessed', 'was_successful']),
        ]

    def __str__(self):
        return f"{self.child.first_name} → {self.theme} ({'Success' if self.was_successful else 'Fail'})"


# ---------------------------------
# 5. Teacher Activity Logs
# ---------------------------------
class TeacherActivityLog(models.Model):

    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
        ('started', 'Started'),
        ('completed', 'Completed'),
    ]

    id = models.BigAutoField(primary_key=True)

    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='teacher_activity_logs',
        limit_choices_to={'role': 'teacher'}
    )

    preschool = models.ForeignKey(
        'preschools.Preschool',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teacher_activity_logs'
    )

    theme = models.CharField(max_length=100, blank=True, null=True)
    sub_theme = models.CharField(max_length=100, blank=True, null=True)
    activity_name = models.CharField(max_length=255, blank=True, null=True)

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='success'
    )

    activity_date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'teacher_activity_logs'
        indexes = [
            models.Index(fields=['teacher']),
            models.Index(fields=['preschool']),
            models.Index(fields=['activity_date']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"TeacherActivityLog {self.teacher.get_full_name()} {self.activity_name or ''}"
    
def get_teacher_preschool(user):
    from django.apps import apps

    PreschoolTeacher = apps.get_model('preschools', 'PreschoolTeacher')
    relation = PreschoolTeacher.objects.filter(
        teacher=user,
        is_active=True,
        is_approved=True,
        is_primary=True
    ).select_related('preschool').first()
    if relation:
        return relation.preschool

    relation = PreschoolTeacher.objects.filter(
        teacher=user,
        is_active=True,
        is_approved=True
    ).select_related('preschool').first()
    return relation.preschool if relation else None


# ---------------------------------
# 6. Preschool Enrollment Opt-In
# ---------------------------------
class PreschoolEnrollmentOptIn(models.Model):
    CONTACT_METHOD_CHOICES = [
        ('whatsapp', 'WhatsApp'),
        ('portal', 'Portal Prompt'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent = models.OneToOneField(User, on_delete=models.CASCADE)
    contact_method = models.CharField(max_length=20, choices=CONTACT_METHOD_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'preschool_enrollment_optins'

    def __str__(self):
        return f"Opt-in: {self.parent} via {self.contact_method}"


# ---------------------------------
# 6. APK Version Management
# ---------------------------------
def apk_upload_path(instance, filename):
    return "apk/haap_uma.apk"


class ApkVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    version_name = models.CharField(max_length=20)

    apk_file = models.FileField(upload_to=apk_upload_path, blank=True, null=True)
    download_url = models.URLField(max_length=500, blank=True, null=True)

    is_latest = models.BooleanField(default=False)
    released_at = models.DateTimeField(auto_now_add=True)

    def get_download_url(self):
        if self.download_url:
            return self.download_url
        if self.apk_file:
            return self.apk_file.url
        return ""

    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old = ApkVersion.objects.get(pk=self.pk)
                new_file_name = self.apk_file.name if self.apk_file else ""
                if old.apk_file and old.apk_file.name != new_file_name:
                    if old.apk_file.storage.exists(old.apk_file.name):
                        old.apk_file.storage.delete(old.apk_file.name)
            except ApkVersion.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        if self.is_latest:
            ApkVersion.objects.exclude(pk=self.pk).update(is_latest=False)

    def delete(self, *args, **kwargs):
        if self.apk_file:
            storage, name = self.apk_file.storage, self.apk_file.name
            if storage.exists(name):
                storage.delete(name)
        super().delete(*args, **kwargs)

    class Meta:
        db_table = "apk_versions"

    def __str__(self):
        return f"APK v{self.version_name}"

    
# ---------------------------------
# 7. App-wide Notifications
# ---------------------------------
class AppNotification(models.Model):
    TYPE_CHOICES = [
        ('apk_update', 'APK Update'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='app_notifications',
    )
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    action_url = models.CharField(max_length=500, blank=True, default='')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'app_notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.notification_type}] → {self.recipient}"


# ---------------------------------
# 8. WhatsApp Message Log
# ---------------------------------
class WhatsAppMessage(models.Model):
    TEMPLATE_CHOICES = [
        ('verification', 'Account Verification'),
        ('monthly_report', 'Monthly Progress Report'),
        ('enrollment_info', 'Preschool Enrollment Info'),
    ]
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('delivered', 'Delivered'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    to_number = models.CharField(max_length=15)
    template_type = models.CharField(max_length=30, choices=TEMPLATE_CHOICES)
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    class Meta:
        db_table = 'whatsapp_messages'
        indexes = [
            models.Index(fields=['to_number']),
            models.Index(fields=['template_type', 'sent_at']),
        ]

    def __str__(self):
        return f" WhatsApp → {self.to_number} [{self.template_type}] "


class ActivityResult(models.Model):
    """Stores activity results linked to a parent (pid) and a student/child (sid).

    The database column names remain `pid` and `sid` for compatibility, but
    at the ORM level they are proper ForeignKey relations to `User` and `Child`.
    """
    STATUS_CHOICES = (
        ("access", "Access"),
        ("completed", "Completed"),
        ("incompleted", "Incompleted"),
    )
    id = models.AutoField(primary_key=True)
    
    parent = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_results',
        db_column='pid'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="access"
    )
    student = models.ForeignKey(
        Child,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_results',
        db_column='sid'
    )
   
    category1 = models.TextField(null=True, blank=True)
    category2 = models.TextField(null=True, blank=True)
    category3 = models.TextField(null=True, blank=True)

    activity_name = models.TextField(null=True, blank=True)
    activity_result = models.CharField(max_length=100, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'activity_result'
        indexes = [
            models.Index(fields=['parent']),
            models.Index(fields=['student']),
            models.Index(fields=['-created_at'], name='activity_result_created_at_idx'),
        ]

    def __str__(self):
        return f"ActivityResult {self.id} ({self.activity_name}) -> {self.activity_result}"


# ---------------------------------
# 9. Audit Log
# ---------------------------------
class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('login',           'Login'),
        ('logout',          'Logout'),
        ('login_failed',    'Login Failed'),
        ('create',          'Kria'),
        ('update',          'Atualiza'),
        ('delete',          'Apaga'),
        ('upload',          'Upload'),
        ('download',        'Download'),
        ('export',          'Export'),
        ('password_change', 'Muda Password'),
        ('password_reset',  'Reset Password'),
        ('activate',        'Ativasaun'),
        ('deactivate',      'Dezativasaun'),
        ('role_change',     'Muda Papel'),
        ('other',           'Seluk'),
    ]
    STATUS_CHOICES = [
        ('success', 'Suksesu'),
        ('failed',  'Falha'),
    ]

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user         = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='audit_logs',
    )
    username     = models.CharField(max_length=255, blank=True)
    action       = models.CharField(max_length=50, choices=ACTION_CHOICES)
    module       = models.CharField(max_length=100, blank=True)
    description  = models.TextField(blank=True)
    record_id    = models.CharField(max_length=255, blank=True)
    record_name  = models.CharField(max_length=500, blank=True)
    previous_value = models.JSONField(null=True, blank=True)
    new_value    = models.JSONField(null=True, blank=True)
    ip_address   = models.GenericIPAddressField(null=True, blank=True)
    user_agent   = models.TextField(blank=True)
    browser      = models.CharField(max_length=200, blank=True)
    os_info      = models.CharField(max_length=200, blank=True)
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='success')
    timestamp    = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action']),
            models.Index(fields=['module']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.username} → {self.action}"

