from django.db import models

# Create your models here.
import uuid
from django.db import models
from core.models import Child, User
from preschools.models import Preschool

class Classroom(models.Model):
    GROUP_CHOICES = [
        ('A', 'Grupo A'),
        ('B', 'Grupo B'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    preschool = models.ForeignKey(
        Preschool,
        on_delete=models.CASCADE,
        related_name='classrooms'
    )

    name = models.CharField(max_length=100)

    teacher = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='classrooms',
        limit_choices_to={'role': 'teacher'}
    )

    group = models.CharField(
        max_length=1,
        choices=GROUP_CHOICES,
        default='A',
      
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'classrooms'
        unique_together = ('preschool', 'name')

    @property
    def class_name(self):
        return self.name

    def __str__(self):
        teacher_name = self.teacher.get_full_name() if self.teacher else 'No teacher'
        return f"{self.name} ({self.preschool.name}) [{self.group}] - {teacher_name}"
    


class ClassroomChild(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )

    child = models.ForeignKey(
        Child,
        on_delete=models.CASCADE,
        related_name='classroom_history'
    )

    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('classroom', 'child')