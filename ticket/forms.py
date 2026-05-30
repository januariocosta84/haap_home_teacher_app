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
                'class': 'form-select',
                'required': False
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'classroom': 'Sala Aula (Opcionál)',
            'priority': 'Prioridade',
        }

    def __init__(self, *args, **kwargs):
        self.teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        if self.teacher:
            self.fields['classroom'].queryset = Classroom.objects.filter(
                preschool__in=self.teacher.classrooms.all().values_list('preschool', flat=True)
            ).distinct()
        else:
            self.fields['classroom'].queryset = Classroom.objects.none()


class SupportTicketItemForm(forms.ModelForm):
    """Form for individual support ticket items"""

    class Meta:
        model = SupportTicketItem
        fields = ['item_type', 'details', 'preferred_format', 'app_features_to_learn']
        widgets = {
            'item_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'details': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Fornese detalhes kona-ba problema ka husu nee (opcionál)'
            }),
            'preferred_format': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: hadau hadap malu, vídeo guia, workshop ho grupu, 1:1'
            }),
            'app_features_to_learn': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ex: navigasaun, konfigurasaun, jestaun klase'
            }),
        }
        labels = {
            'item_type': 'Tipu Husu',
            'details': 'Detalhes',
            'preferred_format': 'Formatu Preferidu (ba Husu Formasaun)',
            'app_features_to_learn': 'Karaterístika Aplikasaun Nian ne\'e Hakarak Aprende (ba Husu Formasaun)',
        }

    def clean(self):
        cleaned_data = super().clean()
        item_type = cleaned_data.get('item_type')
        preferred_format = cleaned_data.get('preferred_format')
        app_features = cleaned_data.get('app_features_to_learn')

        # Check if training request fields are filled when appropriate
        if item_type == 'general_training':
            if not preferred_format and not app_features:
                raise forms.ValidationError(
                    'Favor fornese informasaun kona-ba formatu preferidu ka karaterístika aplikasaun nian.'
                )

        return cleaned_data


class SupportTicketItemFormSet(forms.BaseInlineFormSet):
    """Formset for managing multiple support ticket items"""

    def clean(self):
        super().clean()
        # Ensure at least one item is provided
        if not any(self.cleaned_data) or all(self.management_form.cleaned_data['TOTAL_FORMS'] == 0):
            raise forms.ValidationError('Favor hili pelomenu ida item ba husu.')
