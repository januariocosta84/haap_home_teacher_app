from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView

from klase.models import Classroom

from .forms import EquipmentForm
from .models import Equipment


class EquipmentCreateView(CreateView):

    model = Equipment
    form_class = EquipmentForm
    template_name = 'equipment/equipment_form.html'
    success_url = reverse_lazy('equipment-list')

    def form_valid(self, form):

        messages.success(
            self.request,
            'Ekipamentu konsege rejistu ho susesu.'
        )

        return super().form_valid(form)


class EquipmentListView(ListView):

    model = Equipment
    template_name = 'equipment/equipment_list.html'
    context_object_name = 'equipments'
    paginate_by = 10

    def get_queryset(self):

        return Equipment.objects.select_related(
            'preschool',
            'classroom',
            'teacher'
        ).order_by('-created_at')


# AJAX VIEW

def load_classrooms(request):

    preschool_id = request.GET.get('preschool_id')

    classrooms = Classroom.objects.filter(
        preschool_id=preschool_id
    ).values('id', 'name')

    return JsonResponse(list(classrooms), safe=False)
