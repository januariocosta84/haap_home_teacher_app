from django import forms
from core.models import User
from equipment.models import Equipment, EquipmentAssignmentHistory
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
            'status',
            'notes',
        ]

        labels = {
            'equipment_type': 'Tipu Ekipamentu',
            'model_number': 'Modelu',
            'serial_number': 'Numeru Serial',
            'preschool': 'Pre-Escolar',
            'classroom': 'Sala Aula',
            'teacher': 'Professor / Utilizador',
            'status': 'Status',
            'notes': 'Notas',
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

            'status': forms.Select(attrs={
                'class': 'form-select'
            }),

            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notas adisionais (opcionál)'
            }),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields['preschool'].queryset = Preschool.objects.all()

        self.fields['classroom'].queryset = Classroom.objects.none()

        self.fields['teacher'].queryset = User.objects.filter(
            role='teacher'
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

class EquipmentAssignmentForm(forms.Form):
    """Form for changing or deleting equipment assignment"""

    ACTION_CHOICES = [
        ('reassign', 'Halo Atribisaun Fali'),
        ('delete', 'Hamos Atribisaun'),
        ('retire', 'Retira Ekipamentu'),
    ]

    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        label='Aksaun'
    )

    preschool = forms.ModelChoiceField(
        queryset=Preschool.objects.all(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Pre-Escolar Foun (se halo atribisaun fali)',
        empty_label='Hili Pre-Escolar'
    )

    classroom = forms.ModelChoiceField(
        queryset=Classroom.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Sala Aula Foun (se halo atribisaun fali)',
        empty_label='Hili Sala Aula'
    )

    teacher = forms.ModelChoiceField(
        queryset=User.objects.filter(role='teacher'),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Professor Foun (se halo atribisaun fali)',
        empty_label='Hili Professor'
    )

    change_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Razaun ba mudansa (opcionál)'
        }),
        label='Razaun ba Mudansa'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['action'].initial = 'reassign'
        self.fields['classroom'].queryset = Classroom.objects.none()

        if 'preschool' in self.data:
            try:
                preschool_id = self.data.get('preschool')
                self.fields['classroom'].queryset = Classroom.objects.filter(
                    preschool_id=preschool_id
                )
            except (ValueError, TypeError):
                pass

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')

        if action == 'reassign':
            preschool = cleaned_data.get('preschool')
            if not preschool:
                self.add_error('preschool', 'Pre-Escolar nee rekeridu atu halo atribisaun fali.')

            classroom = cleaned_data.get('classroom')
            if classroom and preschool and classroom.preschool != preschool:
                self.add_error('classroom', 'Sala aula la pertence ba pre-escolar nee.')

        return cleaned_data
