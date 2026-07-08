from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_appnotification'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('username', models.CharField(blank=True, max_length=255)),
                ('action', models.CharField(choices=[
                    ('login', 'Login'), ('logout', 'Logout'), ('login_failed', 'Login Failed'),
                    ('create', 'Kria'), ('update', 'Atualiza'), ('delete', 'Apaga'),
                    ('upload', 'Upload'), ('download', 'Download'), ('export', 'Export'),
                    ('password_change', 'Muda Password'), ('password_reset', 'Reset Password'),
                    ('activate', 'Ativasaun'), ('deactivate', 'Dezativasaun'),
                    ('role_change', 'Muda Papel'), ('other', 'Seluk'),
                ], max_length=50)),
                ('module', models.CharField(blank=True, max_length=100)),
                ('description', models.TextField(blank=True)),
                ('record_id', models.CharField(blank=True, max_length=255)),
                ('record_name', models.CharField(blank=True, max_length=500)),
                ('previous_value', models.JSONField(blank=True, null=True)),
                ('new_value', models.JSONField(blank=True, null=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('browser', models.CharField(blank=True, max_length=200)),
                ('os_info', models.CharField(blank=True, max_length=200)),
                ('status', models.CharField(choices=[('success', 'Suksesu'), ('failed', 'Falha')], default='success', max_length=20)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='audit_logs',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'db_table': 'audit_logs',
                'ordering': ['-timestamp'],
                'indexes': [
                    models.Index(fields=['-timestamp'], name='audit_timestamp_idx'),
                    models.Index(fields=['user', '-timestamp'], name='audit_user_ts_idx'),
                    models.Index(fields=['action'], name='audit_action_idx'),
                    models.Index(fields=['module'], name='audit_module_idx'),
                    models.Index(fields=['status'], name='audit_status_idx'),
                ],
            },
        ),
    ]
