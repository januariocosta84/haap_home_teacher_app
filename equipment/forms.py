from django import forms

from core.views.user_management import User
from equipment.models import Equipment
from klase.models import Classroom
from preschools.models import Preschool
class EquipmentForm(forms.ModelForm):

    class Meta:
        model = Equipment

        fields = [
            'equipment_type',
            'model_number',
            'serial_number',
            'preschool',
            'classroom',
            'teacher',
        ]

        labels = {
            'equipment_type': 'Tipu Ekipamentu',
            'model_number': 'Modelu',
            'serial_number': 'Númeru Serial',
            'preschool': 'Pre-Escolar',
            'classroom': 'Sala Aula',
            'teacher': 'Professor / Utilizadór',
        }

        widgets = {
            'equipment_type': forms.Select(attrs={
                'class': 'form-select'
            }),

            'model_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Dell Latitude 5420'
            }),

            'serial_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: SN-0001'
            }),

            'preschool': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_preschool'
            }),

            'classroom': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_classroom'
            }),

            'teacher': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields['preschool'].queryset = Preschool.objects.all()

        self.fields['classroom'].queryset = Classroom.objects.none()

        self.fields['teacher'].queryset = User.objects.filter(
            groups__name='Teacher'
        ).distinct()

        self.fields['preschool'].empty_label = 'Hili Pre-Escolar'
        self.fields['classroom'].empty_label = 'Hili Sala Aula'
        self.fields['teacher'].empty_label = 'Hili Professor'

        # Dynamic classroom filter
        if 'preschool' in self.data:
            try:
                preschool_id = self.data.get('preschool')

                self.fields['classroom'].queryset = (
                    Classroom.objects.filter(
                        preschool_id=preschool_id
                    )
                )

            except (ValueError, TypeError):
                pass

        elif self.instance.pk and self.instance.preschool:

            self.fields['classroom'].queryset = (
                Classroom.objects.filter(
                    preschool=self.instance.preschool
                )
            )

    def clean(self):

        cleaned_data = super().clean()

        preschool = cleaned_data.get('preschool')
        classroom = cleaned_data.get('classroom')

        if classroom and preschool:

            if classroom.preschool != preschool:

                self.add_error(
                    'classroom',
                    'Sala aula la pertence ba pre-escolar ne’e.'
                )

        return cleaned_data
