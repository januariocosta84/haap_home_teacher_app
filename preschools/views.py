from django.views.generic import DetailView, ListView, CreateView, TemplateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.core.paginator import Paginator
import json

from core.models import Municipality
from klase.models import Classroom
from .models import Preschool, PreschoolTeacher
from .forms import ClassroomForm, PreschoolForm
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from klase.models import ClassroomChild
from core.models import Child
from klase.forms import ChildCodeEnrollmentForm
from fonte_api import send_whatsapp_message
from core.audit import log_action
from equipment.models import Equipment, EquipmentType


@method_decorator(login_required, name='dispatch')
class PreschoolListView(ListView):
    model = Preschool
    template_name = 'preschools/preschool_list.html'
    context_object_name = 'preschools'
    paginate_by = 10

    def get_queryset(self):
        qs = Preschool.objects.select_related(
            'municipality',
            'administrative_post',
            'suco',
            'aldeia'
        ).order_by('-created_at')

        search = self.request.GET.get('search')
        municipality = self.request.GET.get('municipality')

        if search:
            qs = qs.filter(name__icontains=search)

        if municipality:
            qs = qs.filter(municipality_id=municipality)

        return qs
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['municipalities'] = Municipality.objects.all()

        all_qs = Preschool.objects.select_related('municipality').order_by('name')
        map_entries = []
        for p in all_qs:
            has_gps = bool(p.latitude and p.longitude)
            map_entries.append({
                'name': p.name,
                'lat': float(p.latitude) if has_gps else None,
                'lng': float(p.longitude) if has_gps else None,
                'type': p.preschool_type,
                'type_display': p.get_preschool_type_display(),
                'municipality': p.municipality.name if p.municipality else '',
                'pk': str(p.pk),
                'has_gps': has_gps,
            })
        context['map_data_json'] = json.dumps(map_entries)
        context['map_count'] = all_qs.count()
        context['gps_count'] = all_qs.filter(
            latitude__isnull=False, longitude__isnull=False
        ).count()
        return context


@method_decorator(login_required, name='dispatch')
class PreschoolCreateView(CreateView):
    model = Preschool
    form_class = PreschoolForm
    template_name = 'preschools/preschool_form.html'
    success_url = reverse_lazy('preschools:preschool_list')

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'moe_admin':
            messages.error(request, 'Aksesu negadu.')
            return redirect('core:moe_admin_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        obj = form.instance
        log_action(
            request=self.request, action='create', module='Pre-Eskolár',
            description=f"Kria pre-eskolár: {obj.name}",
            record_id=str(obj.pk), record_name=obj.name,
            new_value={'name': obj.name, 'emis': obj.emis_code, 'type': obj.preschool_type,
                       'municipality': str(obj.municipality)},
        )
        return response

@method_decorator(login_required, name='dispatch')
class PreschoolUpdateView(UpdateView):
    model = Preschool
    form_class = PreschoolForm
    template_name = 'preschools/preschool_form.html'
    success_url = reverse_lazy('preschools:preschool_list')

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'moe_admin':
            messages.error(request, 'Aksesu negadu.')
            return redirect('core:moe_admin_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        old = {f: str(getattr(self.object, f, '') or '') for f in ('name', 'emis_code', 'preschool_type')}
        response = super().form_valid(form)
        obj = form.instance
        log_action(
            request=self.request, action='update', module='Pre-Eskolár',
            description=f"Atualiza pre-eskolár: {obj.name}",
            record_id=str(obj.pk), record_name=obj.name,
            previous_value=old,
            new_value={f: str(getattr(obj, f, '') or '') for f in ('name', 'emis_code', 'preschool_type')},
        )
        return response

@method_decorator(login_required, name='dispatch')
class PreschoolDeleteView(DeleteView):
    model = Preschool
    template_name = 'preschools/preschool_confirm_delete.html'
    success_url = reverse_lazy('preschools:preschool_list')

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'moe_admin':
            messages.error(request, 'Aksesu negadu.')
            return redirect('core:moe_admin_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        obj = self.get_object()
        record_id, record_name = str(obj.pk), obj.name
        response = super().form_valid(form)
        log_action(
            request=self.request, action='delete', module='Pre-Eskolár',
            description=f"Apaga pre-eskolár: {record_name}",
            record_id=record_id, record_name=record_name,
        )
        return response

@method_decorator(login_required, name='dispatch')
class PreschoolDetailView(DetailView):
    model = Preschool
    template_name = 'preschools/preschool_detail.html'
    context_object_name = 'preschool'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        classrooms = self.object.classrooms.select_related('teacher').all()
        context['classrooms'] = classrooms
        from klase.models import ClassroomChild
        classroom_ids = classrooms.values_list('id', flat=True)
        context['student_count'] = ClassroomChild.objects.filter(
            classroom_id__in=classroom_ids
        ).count()
        context['approved_teacher_count'] = self.object.teachers.filter(
            is_active=True,
            is_approved=True,
            teacher__is_active=True,
        ).count()

        # Equipment assigned to this preschool, grouped by type
        eq_qs = (
            Equipment.objects
            .filter(preschool=self.object)
            .select_related('equipment_type')
        )
        eq_by_type = {}
        for eq in eq_qs:
            t = eq.equipment_type
            if t.id not in eq_by_type:
                eq_by_type[t.id] = {
                    'type': t,
                    'total': 0,
                    'active': 0,
                    'damaged': 0,
                    'retired': 0,
                    'inactive': 0,
                }
            eq_by_type[t.id]['total'] += 1
            eq_by_type[t.id][eq.status] = eq_by_type[t.id].get(eq.status, 0) + 1

        context['equipment_by_type'] = sorted(eq_by_type.values(), key=lambda x: x['type'].name)
        context['equipment_total'] = eq_qs.count()
        return context

"""Claim the preschool as a teacher. This allows the user to manage the preschool's classrooms and students."""
class ClaimPreschoolView(LoginRequiredMixin, View):
    def post(self, request, preschool_id):
        if request.user.role != 'teacher':
            messages.error(request, 'Only teachers can request access to a preschool.')
            return redirect('core:login')

        preschool = get_object_or_404(Preschool, id=preschool_id)

        PreschoolTeacher.objects.get_or_create(
            teacher=request.user,
            preschool=preschool,
            defaults={
                'is_primary': False,
                'is_active': True,
                'is_approved': False
            }
        )

        messages.success(request, 'Request submitted. Your preschool claim is pending admin approval.')
        return redirect('preschools:teacher_preschool_list')
    
class TeacherPreschoolListView(LoginRequiredMixin, TemplateView):
    template_name = 'preschools/preschool_list_claim.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'teacher':
            messages.error(request, 'Aksesu negadu.')
            return redirect('core:login')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # all preschools
        preschool_queryset = Preschool.objects.prefetch_related(
            'classrooms'
        ).order_by('name')

        # teacher claims
        claims = PreschoolTeacher.objects.filter(
            teacher=self.request.user,
            is_active=True
        )

        approved_ids = set(
            claims.filter(
                is_approved=True
            ).values_list('preschool_id', flat=True)
        )

        pending_ids = set(
            claims.filter(
                is_approved=False
            ).values_list('preschool_id', flat=True)
        )

        # convert queryset to list so we can attach custom attrs
        preschool_list = list(preschool_queryset)

        for p in preschool_list:
            p.target_classroom = (
                p.classrooms
                .filter(teacher=self.request.user)
                .order_by('created_at')
                .first()
            )

            p.is_claimed = p.id in approved_ids or p.id in pending_ids
            p.is_approved = p.id in approved_ids
            p.is_pending = p.id in pending_ids

        # Pagination
        paginator = Paginator(preschool_list, 5)  # 10 per page
        page_number = self.request.GET.get('page')
        preschools = paginator.get_page(page_number)

        context['preschools'] = preschools
        context['approved_ids'] = list(approved_ids)
        context['pending_ids'] = list(pending_ids)

        return context
    
@login_required
def join_view(request, preschool_id):
    if request.user.role != 'teacher':
        messages.error(request, 'Deit mestri mak bele husu aksesu ba pre-eskolár.')
        return redirect('core:login')

    preschool = get_object_or_404(Preschool, id=preschool_id)

    try:
        relation, created = PreschoolTeacher.objects.get_or_create(
            teacher=request.user,
            preschool=preschool,
            defaults={
                'is_active': True,
                'is_approved': False
            }
        )
    except Exception:
        messages.error(request, 'Akontese erru ikus ba pedidu ida ne\'e. Favor koko fali.')
        return redirect('preschools:teacher_preschool_list')

    if not created:
        if not relation.is_active:
            relation.is_active = True
            relation.save()
            messages.success(request, "Ita nia pedidu ativu fali no hein aprovasaun admin nian.")
        elif not relation.is_approved:
            messages.info(request, "Ita nia pedidu hein aprovasaun admin nian.")
        else:
            messages.info(request, "Ita aprova ona ba pre-eskolár ida ne'e.")
    else:
        messages.success(request, "Pedidu haruka ona. Hein aprovasaun admin nian.")

    log_action(
        request=request, action='other', module='Pre-Eskolár',
        description=f"Profesór {request.user.get_full_name()} husu aksesu ba {preschool.name}",
        record_id=str(preschool.pk), record_name=preschool.name,
    )
    return redirect('preschools:teacher_preschool_list')

@method_decorator(login_required, name='dispatch')
class PreschoolTeacherRequestListView(TemplateView):
    template_name = 'preschools/preschool_teacher_requests.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'moe_admin':
            messages.error(request, 'Aksesu negadu.')
            return redirect('core:moe_admin_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['requests'] = PreschoolTeacher.objects.filter(
            is_active=True,
            is_approved=False
        ).select_related('teacher', 'preschool').order_by('-assigned_at')
        return context

@login_required
def approve_preschool_teacher_request(request, request_id):
    if request.user.role != 'moe_admin':
        messages.error(request, 'Aksesu negadu.')
        return redirect('core:moe_admin_dashboard')

    preschool_teacher = get_object_or_404(
        PreschoolTeacher,
        id=request_id,
        is_active=True,
        is_approved=False
    )
    preschool_teacher.is_approved = True
    preschool_teacher.save()

    message = (
        f"Hello {preschool_teacher.teacher.first_name},\n\n"
        f"Ola {preschool_teacher.preschool.name} ita nia pedidu aprovadu. "
        "Iha tempu badak ita sei hetan ativasaun ba klase nian."
    )
    try:
        send_whatsapp_message(preschool_teacher.teacher.whatsapp_number, message)
        messages.success(request, 'Pedidu profesór pre-eskolár nian aprova ona no notifikasaun WhatsApp haruka ona.')
    except Exception as exc:
        messages.warning(request, f'Profesór pre-eskolár nian aprova ona, maibé notifikasaun WhatsApp la konsege haruka. {exc}')

    log_action(
        request=request, action='activate', module='Pre-Eskolár',
        description=f"Aprova profesór {preschool_teacher.teacher.get_full_name()} ba {preschool_teacher.preschool.name}",
        record_id=str(preschool_teacher.pk),
        record_name=preschool_teacher.teacher.get_full_name(),
    )
    return redirect('preschools:teacher_request_list')

class UnclaimPreschoolView(LoginRequiredMixin, View):
    def post(self, request, preschool_id):
        preschool_teacher = get_object_or_404(
            PreschoolTeacher,
            teacher=request.user,
            preschool_id=preschool_id,
            is_active=True
        )

        preschool_teacher.is_active = False
        preschool_teacher.save()

        messages.success(request, 'Preschool unclaimed successfully.')
        return redirect('teacher_preschool_list')

class PrimaryClaimPreschoolView(LoginRequiredMixin, View):
    def post(self, request, preschool_id):
        preschool_teacher = get_object_or_404(
            PreschoolTeacher,
            teacher=request.user,
            preschool_id=preschool_id,
            is_active=True
        )

        # Set all other claims for this preschool to not primary
        PreschoolTeacher.objects.filter(
            preschool_id=preschool_id,
            is_active=True
        ).update(is_primary=False)

        # Set this claim as primary
        preschool_teacher.is_primary = True
        preschool_teacher.save()

        messages.success(request, 'Preschool set as primary successfully.')
        return redirect('teacher_preschool_list')
    
class UnclaimPrimaryPreschoolView(LoginRequiredMixin, View):
    def post(self, request, preschool_id):
        preschool_teacher = get_object_or_404(
            PreschoolTeacher,
            teacher=request.user,
            preschool_id=preschool_id,
            is_active=True
        )

        preschool_teacher.is_primary = False
        preschool_teacher.save()

        messages.success(request, 'Preschool unclaimed as primary successfully.')
        return redirect('teacher_preschool_list')


class ClassroomCreateView(LoginRequiredMixin, CreateView):
    model = Classroom
    form_class = ClassroomForm
    template_name = "preschools/classroom_form.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'moe_admin':
            messages.error(request, "Aksesu negadu.")
            return redirect('core:moe_admin_dashboard')

        self.preschool = get_object_or_404(
            Preschool,
            id=kwargs["id"]
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['preschool'] = self.preschool
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['preschool'] = self.preschool
        return context

    def form_valid(self, form):
        classroom = form.save(commit=False)
        classroom.preschool = self.preschool

        teacher = form.cleaned_data.get('teacher')
        if teacher:
            assigned = PreschoolTeacher.objects.filter(
                teacher=teacher,
                preschool=self.preschool,
                is_active=True,
                is_approved=True,
            ).exists()
            if not assigned:
                form.add_error(
                    'teacher',
                    f"Profesór '{teacher.get_full_name()}' seidauk atribuidu ba pre-eskolár '{self.preschool.name}'. "
                    "Favor atribui profesór ba pre-eskolár ne'e molok atribui klase."
                )
                return self.form_invalid(form)

        try:
            classroom.save()

            # SUCCESS MESSAGE
            messages.success(self.request, "Sala aula kria ho susesu.")
            log_action(
                request=self.request, action='create', module='Sala Aula',
                description=f"Kria sala aula: {classroom.name} iha {self.preschool.name}",
                record_id=str(classroom.pk), record_name=classroom.name,
                new_value={'name': classroom.name, 'preschool': self.preschool.name},
            )
            return redirect("preschools:preschool_detail", pk=self.preschool.id)

        except IntegrityError:
            # FIELD ERROR
            form.add_error(
                'name',
                "Sala ida ho naran ida ne'e eziste ona ba pre-eskolár ida ne'e."
            )

            # GLOBAL ERROR MESSAGE
            messages.error(
                self.request,
                "Labele kria sala aula. Naran ne'e eziste ona."
            )

            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            "Favor halo koreksaun ba dadus ne'ebe sala."
        )
        return super().form_invalid(form)

class ClassroomDetailView(LoginRequiredMixin, DetailView):
    model = Classroom
    template_name = "klase/classroom_detail.html"
    context_object_name = "classroom"
    pk_url_kwarg = "id"

    def dispatch(self, request, *args, **kwargs):
        classroom = self.get_object()
        if request.user.role == 'teacher' and classroom.teacher != request.user:
            messages.error(request, 'Aksesu negadu.')
            return redirect('core:teacher_dashboard')
        if request.user.role == 'parent':
            messages.error(request, 'Aksesu negadu.')
            return redirect('core:child_list')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        classroom = self.object
        # enrollment form
        context['form'] = ChildCodeEnrollmentForm()
        # students: ClassroomChild instances
        context['students'] = classroom.enrollments.select_related('child').all()
        return context


@login_required
def enroll_child(request, id):
    classroom = get_object_or_404(Classroom, id=id)

    if request.method == 'POST':
        code = request.POST.get('child_code', '').strip()
        if not code:
            from django.contrib import messages
            messages.error(request, 'Please provide a child code.')
            return redirect('preschools:classroom_detail', id=classroom.id)

        try:
            child = Child.objects.get(user_id=code)
        except Child.DoesNotExist:
            from django.contrib import messages
            messages.error(request, 'Kodigu seidauk iha sistema.')
            return redirect('preschools:classroom_detail', id=classroom.id)

        if child.age_group != classroom.group:
            from django.contrib import messages
            messages.error(
                request,
                f"Child group '{child.age_group}' cannot be enrolled in classroom group '{classroom.group}'. Please use the correct A/B group."
            )
            return redirect('preschools:classroom_detail', id=classroom.id)

        ClassroomChild.objects.filter(
            child=child,
            is_active=True
        ).update(is_active=False)

        relation, created = ClassroomChild.objects.get_or_create(
            classroom=classroom,
            child=child,
            defaults={'is_active': True}
        )

        if not created and not relation.is_active:
            relation.is_active = True
            relation.save()

        from django.contrib import messages
        messages.success(request, 'Child enrolled successfully.')
        log_action(
            request=request, action='create', module='Sala Aula',
            description=f"Rejista labarik '{child.first_name}' iha sala '{classroom.name}'",
            record_id=str(classroom.pk), record_name=classroom.name,
            new_value={'child': str(child), 'classroom': classroom.name},
        )

    return redirect('preschools:classroom_detail', id=classroom.id)

class ClassroomUpdateView(LoginRequiredMixin, UpdateView):
    model = Classroom
    form_class = ClassroomForm
    template_name = "preschools/classroom_form.html"
    pk_url_kwarg = "id"

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'moe_admin':
            messages.error(request, 'Aksesu negadu.')
            return redirect('core:moe_admin_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['preschool'] = self.object.preschool
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['preschool'] = self.object.preschool
        return context

    def form_valid(self, form):
        teacher = form.cleaned_data.get('teacher')
        if teacher:
            preschool = self.object.preschool
            assigned = PreschoolTeacher.objects.filter(
                teacher=teacher,
                preschool=preschool,
                is_active=True,
                is_approved=True,
            ).exists()
            if not assigned:
                form.add_error(
                    'teacher',
                    f"Profesór '{teacher.get_full_name()}' seidauk atribuidu ba pre-eskolár '{preschool.name}'. "
                    "Favor atribui profesór ba pre-eskolár ne'e molok atribui klase."
                )
                return self.form_invalid(form)

        old_name = self.object.name
        response = super().form_valid(form)
        obj = form.instance
        messages.success(self.request, "Klass update ho susesu.")
        log_action(
            request=self.request, action='update', module='Sala Aula',
            description=f"Atualiza sala aula: {obj.name}",
            record_id=str(obj.pk), record_name=obj.name,
            previous_value={'name': old_name},
            new_value={'name': obj.name},
        )
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['preschool'] = self.object.preschool
        return context

    def get_success_url(self):
        return reverse_lazy(
            "preschools:preschool_detail",
            kwargs={"pk": self.object.preschool.id}
        )


class ClassroomDeleteView(LoginRequiredMixin, View):
    def post(self, request, id):
        if request.user.role != 'moe_admin':
            messages.error(request, 'Aksesu negadu.')
            return redirect('core:moe_admin_dashboard')

        classroom = get_object_or_404(Classroom, id=id)
        preschool_id = classroom.preschool_id
        classroom_name = classroom.name

        log_action(
            request=request, action='delete', module='Sala Aula',
            description=f"Hasai klase: {classroom_name} husi {classroom.preschool.name}",
            record_id=str(classroom.id), record_name=classroom_name,
        )
        classroom.delete()
        messages.success(request, f"Klase '{classroom_name}' hasai ho susesu.")
        return redirect('preschools:preschool_detail', pk=preschool_id)
