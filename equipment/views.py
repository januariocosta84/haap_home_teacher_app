from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, DeleteView, DetailView
from django.utils import timezone
from django.db.models import Q

from klase.models import Classroom
from preschools.models import Preschool
from core.models import User

from .forms import EquipmentForm, EquipmentAssignmentForm
from .models import Equipment, EquipmentAssignmentHistory


class AdminOnlyMixin(UserPassesTestMixin):
    """Mixin to restrict access to admin users"""
    def test_func(self):
        return self.request.user.role == 'moe_admin'


class EquipmentCreateView(LoginRequiredMixin, AdminOnlyMixin, CreateView):

    model = Equipment
    form_class = EquipmentForm
    template_name = 'equipment/equipment_form.html'
    success_url = reverse_lazy('equipment:equipment_list')

    def form_valid(self, form):
        messages.success(
            self.request,
            'Ekipamentu konsege rejistu ho susesu.'
        )
        return super().form_valid(form)
    def form_invalid(self, form):
        messages.error(self.request, form.errors)
        return super().form_invalid(form)


class EquipmentListView(LoginRequiredMixin, AdminOnlyMixin, ListView):

    model = Equipment
    template_name = 'equipment/equipment_list.html'
    context_object_name = 'equipments'
    paginate_by = 20

    def get_queryset(self):
        queryset = Equipment.objects.select_related(
            'preschool',
            'classroom',
            'teacher'
        ).order_by('-created_at')

        # Filter by equipment type
        equipment_type = self.request.GET.get('equipment_type')
        if equipment_type:
            queryset = queryset.filter(equipment_type=equipment_type)

        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Filter by preschool
        preschool = self.request.GET.get('preschool')
        if preschool:
            queryset = queryset.filter(preschool_id=preschool)

        # Search by serial number or model
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(serial_number__icontains=search) |
                Q(model_number__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['equipment_types'] = Equipment.TYPE_CHOICES
        context['statuses'] = Equipment.STATUS_CHOICES
        context['preschools'] = Preschool.objects.all()
        query = self.request.GET.copy()
        query.pop('page', None)
        context['querystring'] = query.urlencode()
        return context


class EquipmentDetailView(LoginRequiredMixin, AdminOnlyMixin, DetailView):

    model = Equipment
    template_name = 'equipment/equipment_detail.html'
    context_object_name = 'equipment'
    pk_url_kwarg = 'pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['assignment_history'] = (
            self.object.assignment_history.all().order_by('-changed_at')
        )
        return context


class EquipmentUpdateView(LoginRequiredMixin, AdminOnlyMixin, UpdateView):

    model = Equipment
    form_class = EquipmentForm
    template_name = 'equipment/equipment_form.html'

    def get_success_url(self):
        return reverse_lazy('equipment:equipment_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        # Check if assignment changed
        if form.has_changed():
            old_preschool = self.object.preschool
            old_classroom = self.object.classroom
            old_teacher = self.object.teacher

            response = super().form_valid(form)

            # Log the assignment change if relevant fields changed
            if (old_preschool != form.cleaned_data.get('preschool') or
                old_classroom != form.cleaned_data.get('classroom') or
                old_teacher != form.cleaned_data.get('teacher')):

                EquipmentAssignmentHistory.objects.create(
                    equipment=self.object,
                    old_preschool=old_preschool,
                    old_classroom=old_classroom,
                    old_teacher=old_teacher,
                    new_preschool=form.cleaned_data.get('preschool'),
                    new_classroom=form.cleaned_data.get('classroom'),
                    new_teacher=form.cleaned_data.get('teacher'),
                    changed_by=self.request.user,
                    change_reason='Direct equipment update'
                )

            messages.success(
                self.request,
                'Ekipamentu updates ho susesu.'
            )
            return response
        else:
            return super().form_valid(form)


class EquipmentAssignmentChangeView(LoginRequiredMixin, AdminOnlyMixin, UpdateView):

    model = Equipment
    form_class = EquipmentAssignmentForm
    template_name = 'equipment/equipment_assignment_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.pop('instance', None)  # Remove instance for the non-model form
        return kwargs

    def form_valid(self, form):
        action = form.cleaned_data.get('action')
        # self.object is the Equipment instance fetched by get_object() before
        # form_valid runs, so it still holds the original assignment values here.
        old_equipment = self.object

        try:
            if action == 'reassign':
                new_preschool = form.cleaned_data.get('preschool')
                new_classroom = form.cleaned_data.get('classroom')
                new_teacher = form.cleaned_data.get('teacher')

                # Log the assignment change
                EquipmentAssignmentHistory.objects.create(
                    equipment=self.object,
                    old_preschool=old_equipment.preschool,
                    old_classroom=old_equipment.classroom,
                    old_teacher=old_equipment.teacher,
                    new_preschool=new_preschool,
                    new_classroom=new_classroom,
                    new_teacher=new_teacher,
                    changed_by=self.request.user,
                    change_reason=form.cleaned_data.get('change_reason')
                )

                # Update equipment
                self.object.preschool = new_preschool
                self.object.classroom = new_classroom
                self.object.teacher = new_teacher
                self.object.save()

                messages.success(
                    self.request,
                    'Atribisaun ekipamentu updates ho susesu.'
                )

            elif action == 'delete':
                # Log the deletion of assignment
                EquipmentAssignmentHistory.objects.create(
                    equipment=self.object,
                    old_preschool=old_equipment.preschool,
                    old_classroom=old_equipment.classroom,
                    old_teacher=old_equipment.teacher,
                    changed_by=self.request.user,
                    change_reason=form.cleaned_data.get('change_reason') or 'Assignment deleted'
                )

                # Clear assignment
                self.object.preschool = None
                self.object.classroom = None
                self.object.teacher = None
                self.object.save()

                messages.success(
                    self.request,
                    'Atribisaun ekipamentu removidu ho susesu.'
                )

            elif action == 'retire':
                # Log the retirement
                EquipmentAssignmentHistory.objects.create(
                    equipment=self.object,
                    old_preschool=old_equipment.preschool,
                    old_classroom=old_equipment.classroom,
                    old_teacher=old_equipment.teacher,
                    changed_by=self.request.user,
                    change_reason=form.cleaned_data.get('change_reason') or 'Equipment retired'
                )

                # Mark as retired
                self.object.status = 'retired'
                self.object.preschool = None
                self.object.classroom = None
                self.object.teacher = None
                self.object.save()

                messages.success(
                    self.request,
                    'Ekipamentu retiradu ho susesu.'
                )

            return redirect(self.get_success_url())

        except Exception as e:
            messages.error(self.request, f'Erro: {str(e)}')
            return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy('equipment:equipment_detail', kwargs={'pk': self.object.pk})


class EquipmentDeleteView(LoginRequiredMixin, AdminOnlyMixin, DeleteView):

    model = Equipment
    template_name = 'equipment/equipment_confirm_delete.html'
    success_url = reverse_lazy('equipment:equipment_list')

    def form_valid(self, form):
        messages.success(self.request, 'Ekipamentu deleta ho susesu.')
        return super().form_valid(form)


class EquipmentByPreschoolView(LoginRequiredMixin, AdminOnlyMixin, ListView):

    model = Equipment
    template_name = 'equipment/equipment_by_preschool.html'
    context_object_name = 'equipments'
    paginate_by = 20

    def get_queryset(self):
        preschool_id = self.kwargs.get('preschool_id')
        return Equipment.objects.filter(
            preschool_id=preschool_id
        ).select_related('preschool', 'classroom', 'teacher')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        preschool_id = self.kwargs.get('preschool_id')
        context['preschool'] = get_object_or_404(Preschool, pk=preschool_id)
        return context


class EquipmentByClassroomView(LoginRequiredMixin, AdminOnlyMixin, ListView):

    model = Equipment
    template_name = 'equipment/equipment_by_classroom.html'
    context_object_name = 'equipments'
    paginate_by = 20

    def get_queryset(self):
        classroom_id = self.kwargs.get('classroom_id')
        return Equipment.objects.filter(
            classroom_id=classroom_id
        ).select_related('preschool', 'classroom', 'teacher')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        classroom_id = self.kwargs.get('classroom_id')
        context['classroom'] = get_object_or_404(Classroom, pk=classroom_id)
        return context


class EquipmentByTeacherView(LoginRequiredMixin, AdminOnlyMixin, ListView):

    model = Equipment
    template_name = 'equipment/equipment_by_teacher.html'
    context_object_name = 'equipments'
    paginate_by = 20

    def get_queryset(self):
        teacher_id = self.kwargs.get('teacher_id')
        return Equipment.objects.filter(
            teacher_id=teacher_id
        ).select_related('preschool', 'classroom', 'teacher')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher_id = self.kwargs.get('teacher_id')
        context['teacher'] = get_object_or_404(User, pk=teacher_id, role='teacher')
        return context


# AJAX VIEW

def load_classrooms(request):

    preschool_id = request.GET.get('preschool_id')

    classrooms = Classroom.objects.filter(
        preschool_id=preschool_id
    ).values('id', 'name')

    return JsonResponse(list(classrooms), safe=False)
