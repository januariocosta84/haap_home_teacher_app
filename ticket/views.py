# ticket/views.py
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, DetailView
from django.forms import inlineformset_factory
from django.db.models import Q

from core.models import User
from ticket.models import (
    SupportTicket,
    SupportTicketDetail,
    SupportTicketItem,
    SupportTicketMessage,
    Notification,
)
from ticket.forms import (
    SupportTicketForm,
    SupportTicketItemForm,
    SupportTicketUpdateForm,
    TicketReplyForm,
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

class SupportTicketCreateView(LoginRequiredMixin,CreateView):
    model = SupportTicket
    form_class = SupportTicketForm
    template_name = 'ticket/support_ticket_form.html'
    success_url = reverse_lazy('ticket:support-ticket-list')

    # Example data
    equipment_items = [
        ('tablet', 'Tablet'),
        ('projector', 'Projetor'),
        ('speaker', 'Speaker'),
        ('internet', 'Internet'),
        ('other', 'Seluk'),
    ]

    training_items = [
        (
            'app_navigation',
            'Navigasaun Aplikasaun'
        ),
        (
            'attendance',
            'Jestaun Prezensa'
        ),
        (
            'reporting',
            'Relatóriu'
        ),
        (
            'other',
            'Seluk'
        ),
    ]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        teacher = getattr(
            self.request.user,
            'teacher',
            None
        )

       # FIX kwargs
        kwargs['teacher'] = self.request.user
        return kwargs

    def get_context_data(self,**kwargs):
        context = super().get_context_data(**kwargs)
        context['equipment_items'] = self.equipment_items
        context['training_items'] = self.training_items
        return context

    def form_valid(self, form):
        equipment = self.request.POST.getlist('equipment_items')
        training = self.request.POST.getlist('training_items')
        if not equipment and not training:
            form.add_error(None, 'Favor hili menus item ida.')
            return self.form_invalid(form)

        ticket = form.save(commit=False)
        ticket.teacher = self.request.user

        if ticket.classroom:
            ticket.preschool = ticket.classroom.preschool
        else:
            first_classroom = self.request.user.classrooms.select_related('preschool').first()
            if first_classroom:
                ticket.preschool = first_classroom.preschool
            else:
                form.add_error('classroom', 'Preschool la konsege determina.')
                return self.form_invalid(form)

        ticket.is_equipment_request = bool(equipment)
        ticket.is_training_request = bool(training)
        ticket.save()

        for item in equipment:
            SupportTicketDetail.objects.create(
                ticket=ticket,
                category='equipment',
                item_key=item,
                details=self.request.POST.get(f'details_{item}'),
            )

        for item in training:
            SupportTicketDetail.objects.create(
                ticket=ticket,
                category='training',
                item_key=item,
                preferred_format=self.request.POST.get(f'preferred_format_{item}'),
                app_features=self.request.POST.get(f'app_features_{item}'),
            )

        messages.success(self.request, 'Ticket suporta kria ho susesu.')
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, 'Favor korrije erru sira.')
        return super().form_invalid(form)

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

        details = list(self.object.details.all())
        items = list(self.object.items.all())
        detail_map = {detail.item_key: detail for detail in details}
        item_display_map = dict(
            SupportTicketItem.EQUIPMENT_ITEM_CHOICES +
            SupportTicketItem.TRAINING_ITEM_CHOICES
        )

        problem_items = []
        matched_detail_keys = set()

        for item in items:
            detail = detail_map.get(item.item_type)
            if detail:
                matched_detail_keys.add(item.item_type)
            problem_items.append({
                'item': item,
                'detail': detail,
                'label': item.get_item_type_display()
            })

        for detail in details:
            if detail.item_key in matched_detail_keys:
                continue
            label = item_display_map.get(detail.item_key)
            if not label:
                label = f"{detail.get_category_display()} - {detail.item_key}"
            problem_items.append({
                'item': None,
                'detail': detail,
                'label': label
            })

        context['items'] = items
        context['details'] = details
        context['problem_items'] = problem_items

        context['ticket_messages'] = self.object.messages.select_related('sender').all()
        context['reply_form'] = TicketReplyForm()
        return context
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = TicketReplyForm(request.POST)

        if form.is_valid():
            reply = form.save(commit=False)
            reply.ticket = self.object
            reply.sender = request.user
            reply.sender_type = 'admin' if request.user.role == 'moe_admin' else 'teacher'
            reply.save()
            if request.user.role == 'moe_admin' and self.object.status == 'open':
                self.object.status = 'in_progress'
                self.object.save()
            messages.success(request, 'Komentariu enviadu.')
        return redirect('ticket:support-ticket-detail', pk=self.object.pk)


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

        # Filter by ticket type
        ticket_type = self.request.GET.get('ticket_type')
        if ticket_type == 'equipment':
            queryset = queryset.filter(is_equipment_request=True, is_training_request=False)
        elif ticket_type == 'training':
            queryset = queryset.filter(is_training_request=True, is_equipment_request=False)
        elif ticket_type == 'both':
            queryset = queryset.filter(is_equipment_request=True, is_training_request=True)

        if self.request.user.role == 'moe_admin':
            teacher_id = self.request.GET.get('teacher')
            if teacher_id:
                queryset = queryset.filter(teacher_id=teacher_id)

        return queryset.select_related('teacher', 'preschool').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statuses'] = SupportTicket.STATUS_CHOICES
        context['ticket_type_choices'] = [
            ('', 'Hili Tipu'),
            ('equipment', 'Ekipamentu'),
            ('training', 'Formasaun'),
            ('both', 'Ekipamentu no Formasaun'),
        ]
        context['current_ticket_type'] = self.request.GET.get('ticket_type', '')
        if self.request.user.role == 'moe_admin':
            context['teachers'] = User.objects.filter(role='teacher').order_by('first_name', 'last_name')
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


from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST


@login_required
def notification_unread_count(request):
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'count': count})


@login_required
def notification_list(request):
    notifications = (
        Notification.objects
        .filter(recipient=request.user)
        .select_related('ticket')
        .order_by('-created_at')[:20]
    )
    data = [
        {
            'id': str(n.id),
            'type': n.notification_type,
            'title': n.title,
            'message': n.message,
            'is_read': n.is_read,
            'ticket_id': str(n.ticket.id),
            'ticket_number': n.ticket.ticket_number,
            'created_at': n.created_at.strftime('%d/%m/%Y %H:%M'),
        }
        for n in notifications
    ]
    return JsonResponse({'notifications': data})


@login_required
@require_POST
def notification_mark_read(request, notification_id):
    n = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    n.is_read = True
    n.save(update_fields=['is_read'])
    return JsonResponse({'ok': True})


@login_required
@require_POST
def notification_mark_all_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'ok': True})
