# ticket/forms.py
from django import forms
from ticket.models import SupportTicket, SupportTicketItem
from core.models import User
from preschools.models import Preschool
from klase.models import Classroom


class SupportTicketForm(forms.ModelForm):
    """Form for creating support tickets"""

    class Meta:
        model = SupportTicket
        fields = ['classroom', 'priority']
        widgets = {
            'classroom': forms.Select(attrs={
                'class': 'form-select shadow-sm',
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select shadow-sm',
            }),
        }
        labels = {
            'classroom': 'Sala Aula (Opsional)',
            'priority': 'Prioridade',
        }
        help_texts = {
            'classroom': 'Hili sala aula se problema refere ba sala aula espesífika.',
        }

    def __init__(self, *args, **kwargs):
        self.teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)

        self.fields['classroom'].widget.attrs.update({
            'class': 'form-select shadow-sm'
        })

        self.fields['priority'].widget.attrs.update({
            'class': 'form-select shadow-sm'
        })

        if self.teacher:
            self.fields['classroom'].queryset = Classroom.objects.filter(
                preschool__in=self.teacher.classrooms.all()
                .values_list('preschool', flat=True)
            ).distinct()
        else:
            self.fields['classroom'].queryset = Classroom.objects.none()

        self.fields['classroom'].empty_label = '— Hili Sala Aula —'


class SupportTicketUpdateForm(forms.ModelForm):
    """Form for updating support tickets with Bootstrap styling"""

    class Meta:
        model = SupportTicket
        fields = ['status', 'priority', 'resolution_note']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-select shadow-sm',
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select shadow-sm',
            }),
            'resolution_note': forms.Textarea(attrs={
                'class': 'form-control shadow-sm',
                'rows': 5,
                'placeholder': 'Fornece uma nota de resolução para o ticket...',
            }),
        }
        labels = {
            'status': 'Status',
            'priority': 'Prioridade',
            'resolution_note': 'Nota de Resolução',
        }


class SupportTicketItemForm(forms.ModelForm):
    """Form for individual support ticket items"""

    class Meta:
        model = SupportTicketItem
        fields = [
            'item_type',
            'details',
            'preferred_format',
            'app_features_to_learn'
        ]

        widgets = {
            'item_type': forms.Select(attrs={
                'class': 'form-select shadow-sm',
            }),

            'details': forms.Textarea(attrs={
                'class': 'form-control shadow-sm',
                'rows': 4,
                'placeholder': 'Deskreve problema ka nesesidade ne\'ebé ita hasoru...',
            }),

            'preferred_format': forms.TextInput(attrs={
                'class': 'form-control shadow-sm',
                'placeholder': 'Ex: Enkontru direta, Zoom, Workshop, Video Tutorial',
            }),

            'app_features_to_learn': forms.Textarea(attrs={
                'class': 'form-control shadow-sm',
                'rows': 4,
                'placeholder': 'Ex: Jestaun estudante, Relatóriu, Attendance, Dashboard',
            }),
        }

        labels = {
            'item_type': 'Tipu Husu',
            'details': 'Detalhes Problema / Husu',
            'preferred_format': 'Formatu Formasaun Preferidu',
            'app_features_to_learn': 'Karakterístika Aplikasaun ne\'ebé Hakarak Aprende',
        }

        help_texts = {
            'preferred_format':
                'Preense bainhira husu formasaun.',
            'app_features_to_learn':
                'Lista funsionalidade sira ne\'ebé ita hakarak aprende.',
        }

    def clean(self):
        cleaned_data = super().clean()

        item_type = cleaned_data.get('item_type')
        preferred_format = cleaned_data.get('preferred_format')
        app_features = cleaned_data.get('app_features_to_learn')

        if item_type == 'general_training':
            if not preferred_format and not app_features:
                raise forms.ValidationError(
                    'Favor fornese informasaun kona-ba formatu preferidu ka karakterístika aplikasaun ne\'ebé hakarak aprende.'
                )

        return cleaned_data


class SupportTicketItemFormSet(forms.BaseInlineFormSet):
    """Formset for managing multiple support ticket items"""

    def clean(self):
        super().clean()

        valid_forms = [
            form for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False)
        ]

        if not valid_forms:
            raise forms.ValidationError(
                'Favor aumenta pelumenus ida item ba pedidu suporti.'
            )