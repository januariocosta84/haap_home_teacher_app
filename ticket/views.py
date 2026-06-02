# ticket/views.py
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, DetailView
from django.forms import inlineformset_factory
from django.db.models import Q

from ticket.models import SupportTicket, SupportTicketItem
from ticket.forms import (
    SupportTicketForm,
    SupportTicketItemForm,
    SupportTicketUpdateForm,
)
from preschools.models import Preschool

app_name = 'ticket'

class TeacherOnlyMixin(UserPassesTestMixin):
    """Mixin to restrict access to teacher users"""
    def test_func(self):
        return self.request.user.role == 'teacher'


class AdminOnlyMixin(UserPassesTestMixin):
    """Mixin to restrict access to admin users"""
    def test_func(self):
        return self.request.user.role == 'moe_admin'


class SupportTicketCreateView(TeacherOnlyMixin, LoginRequiredMixin, CreateView):
    """View for teachers to create support tickets"""

    model = SupportTicket
    form_class = SupportTicketForm
    template_name = 'ticket/support_ticket_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['teacher'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Set the current teacher and their preschool
        form.instance.teacher = self.request.user

        # Get the preschool from the teacher's first classroom
        teacher_classrooms = self.request.user.classrooms.all()
        if teacher_classrooms.exists():
            form.instance.preschool = teacher_classrooms.first().preschool
        else:
            # If teacher has no classroom, try to get from request or use first available
            messages.error(self.request, 'Mestri nee nao iha klase asosiadu.')
            return self.form_invalid(form)

        self.object = form.save()

        # Redirect to add items
        return redirect('ticket:support-ticket-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['equipment_items'] = [
            ('projector_lamp', '1. Troka lampada projetor'),
            ('miracast_config', '2. Ajuda atu halo konfigurasaun Miracast (tablet Android ba projetor Epson)'),
            ('projector_support', '3. Suporta projetor - hadia ka troka'),
            ('screen_problem', '4. Tela klen - problema'),
            ('tablet_technical', '5. Tablet - problema tekniku'),
            ('tablet_lost', '6. Tablet - naok'),
            ('tablet_damaged', '7. Tablet - estragu'),
            ('projector_damaged', '8. Projetor - estragu ka la funsiona laos ho lampada'),
            ('cable_adapter', '9. Problema ho kabelu ka adaptador (HDMI, USB-C, etc.)'),
            ('other_equipment', '10. Problema seluk ho ekipamentu AV iha sala aula'),
        ]
        context['training_items'] = [
            ('general_training', '11. Husu formasaun geral ba mestri kona-ba uza aplikasaun nee ba ensinu'),
        ]
        return context


class SupportTicketAddItemsView(TeacherOnlyMixin, LoginRequiredMixin, UpdateView):
    """View for adding items to a support ticket"""

    model = SupportTicket
    fields = []
    template_name = 'ticket/support_ticket_items_form.html'
    pk_url_kwarg = 'pk'

    def test_func(self):
        """Ensure user is the ticket creator"""
        return super().test_func() and self.get_object().teacher == self.request.user

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Process form data for ticket items
        equipment_items = request.POST.getlist('equipment_items')
        training_items = request.POST.getlist('training_items')

        # Flag which type of request this is
        if equipment_items:
            self.object.is_equipment_request = True
        if training_items:
            self.object.is_training_request = True

        self.object.save()

        # Create ticket items
        for item_type in equipment_items:
            details = request.POST.get(f'details_{item_type}', '')
            SupportTicketItem.objects.create(
                ticket=self.object,
                item_type=item_type,
                details=details if details else None
            )

        for item_type in training_items:
            preferred_format = request.POST.get(f'preferred_format_{item_type}', '')
            app_features = request.POST.get(f'app_features_{item_type}', '')
            SupportTicketItem.objects.create(
                ticket=self.object,
                item_type=item_type,
                preferred_format=preferred_format if preferred_format else None,
                app_features_to_learn=app_features if app_features else None
            )

        if not equipment_items and not training_items:
            messages.error(request, 'Favor hili pelomenu ida item.')
            return self.get(request, *args, **kwargs)

        messages.success(
            request,
            f'Husu suporta konsege kria ho susesu. Tiket numeru: {self.object.ticket_number}'
        )
        return redirect('ticket:support-ticket-detail', pk=self.object.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['equipment_items'] = [
            ('projector_lamp', '1. Troka lampada projetor'),
            ('miracast_config', '2. Ajuda atu halo konfigurasaun Miracast (tablet Android ba projetor Epson)'),
            ('projector_support', '3. Suporta projetor - hadia ka troka'),
            ('screen_problem', '4. Tela klen - problema'),
            ('tablet_technical', '5. Tablet - problema tekniku'),
            ('tablet_lost', '6. Tablet - naok'),
            ('tablet_damaged', '7. Tablet - estragu'),
            ('projector_damaged', '8. Projetor - estragu ka la funsiona laos ho lampada'),
            ('cable_adapter', '9. Problema ho kabelu ka adaptador (HDMI, USB-C, etc.)'),
            ('other_equipment', '10. Problema seluk ho ekipamentu AV iha sala aula'),
        ]
        context['training_items'] = [
            ('general_training', '11. Husu formasaun geral ba mestri kona-ba uza aplikasaun nee ba ensinu'),
        ]
        context['existing_items'] = self.object.items.all()
        return context


class SupportTicketDetailView(LoginRequiredMixin, DetailView):
    """View for displaying support ticket details"""

    model = SupportTicket
    template_name = 'ticket/support_ticket_detail.html'
    context_object_name = 'ticket'
    pk_url_kwarg = 'pk'

    def get_queryset(self):
        # Teachers see their own tickets, admins see all
        if self.request.user.role == 'teacher':
            return SupportTicket.objects.filter(teacher=self.request.user)
        elif self.request.user.role == 'moe_admin':
            return SupportTicket.objects.all()
        return SupportTicket.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        return context


class SupportTicketListView(LoginRequiredMixin, ListView):
    """List view for support tickets"""

    model = SupportTicket
    template_name = 'ticket/support_ticket_list.html'
    context_object_name = 'tickets'
    paginate_by = 20

    def get_queryset(self):
        if self.request.user.role == 'teacher':
            # Teachers see only their own tickets
            queryset = SupportTicket.objects.filter(
                teacher=self.request.user
            )
        elif self.request.user.role == 'moe_admin':
            # Admins see all tickets
            queryset = SupportTicket.objects.all()
        else:
            queryset = SupportTicket.objects.none()

        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Filter by ticket number
        ticket_number = self.request.GET.get('ticket_number')
        if ticket_number:
            queryset = queryset.filter(ticket_number__icontains=ticket_number)

        return queryset.select_related('teacher', 'preschool').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statuses'] = SupportTicket.STATUS_CHOICES
        return context


class SupportTicketUpdateView(AdminOnlyMixin, LoginRequiredMixin, UpdateView):
    """Admin view for updating support ticket status"""

    model = SupportTicket
    form_class = SupportTicketUpdateForm
    template_name = 'ticket/support_ticket_update.html'

    def get_success_url(self):
        return reverse_lazy('ticket:support-ticket-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        if form.cleaned_data.get('status') == 'resolved':
            from django.utils import timezone
            form.instance.resolved_at = timezone.now()

        messages.success(self.request, 'Tiket updates ho susesu.')
        return super().form_valid(form)


def get_ticket_by_number(request):
    """AJAX endpoint to get ticket details by ticket number"""
    ticket_number = request.GET.get('ticket_number')

    if not ticket_number:
        return JsonResponse({'error': 'Numeru tiket nee rekeridu.'}, status=400)

    ticket = get_object_or_404(SupportTicket, ticket_number=ticket_number)

    return JsonResponse({
        'id': str(ticket.id),
        'ticket_number': ticket.ticket_number,
        'teacher': str(ticket.teacher),
        'preschool': ticket.preschool.name,
        'status': ticket.status,
        'created_at': ticket.created_at.isoformat(),
        'items_count': ticket.items.count(),
    })
