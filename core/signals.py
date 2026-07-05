from django.apps import apps
from django.contrib.auth.signals import user_logged_in, user_logged_out
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


# def _create_teacher_activity_log(user, activity_name):
#     if user.role != 'teacher':
#         return

#     TeacherActivityLog = apps.get_model('core', 'TeacherActivityLog')
#     TeacherActivityLog.objects.create(
#         teacher=user,
#         preschool=get_teacher_preschool(user),
#         activity_name=activity_name,
#         status='success',
#     )


# @receiver(user_logged_in)
# def teacher_logged_in(sender, request, user, **kwargs):
#     _create_teacher_activity_log(user, 'login', 'Teacher login')


# @receiver(user_logged_out)
# def teacher_logged_out(sender, request, user, **kwargs):
#     if user is None:
#         return
#     _create_teacher_activity_log(user, 'logout', 'Teacher logout')
