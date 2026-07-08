from django.apps import apps
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from .models import User, get_teacher_preschool

@receiver(pre_save, sender=User)
def delete_old_image(sender, instance, **kwargs):
    if not instance.pk:
        return  # new user, no old image

    try:
        old_user = User.objects.get(pk=instance.pk)
    except User.DoesNotExist:
        return

    # If image changed, delete the old file
    if old_user.image and old_user.image != instance.image:
        old_user.image.delete(save=False)

@receiver(post_delete, sender=User)
def delete_image_on_user_delete(sender, instance, **kwargs):
    if instance.image and instance.image.name != "defaults/user.png":
        instance.image.delete(save=False)


# ── Audit log signals ────────────────────────────────────────────────────────

@receiver(user_logged_in)
def audit_user_login(sender, request, user, **kwargs):
    from core.audit import log_action
    log_action(
        request=request, user=user,
        action='login', module='Auth',
        description=f'{user.get_full_name() or user.username} login ho susesu.',
        status='success',
    )


@receiver(user_logged_out)
def audit_user_logout(sender, request, user, **kwargs):
    if user is None:
        return
    from core.audit import log_action
    log_action(
        request=request, user=user,
        action='logout', module='Auth',
        description=f'{user.get_full_name() or user.username} logout.',
        status='success',
    )


@receiver(user_login_failed)
def audit_login_failed(sender, credentials, request, **kwargs):
    from core.audit import log_action
    attempted = credentials.get('username', '—')
    log_action(
        request=request, user=None,
        action='login_failed', module='Auth',
        description=f'Login falha ho username/number: {attempted}',
        record_name=attempted,
        username=attempted,
        status='failed',
    )
