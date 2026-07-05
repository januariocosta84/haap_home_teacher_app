from django import forms

from core.models import AdministrativePost, Aldeia, Municipality, Suco
from .models import Preschool
from django import forms
from klase.models import Classroom


class PreschoolForm(forms.ModelForm):

    class Meta:
        model = Preschool

        fields = [
            'name',
            'municipality',
            'administrative_post',
            'suco',
            'aldeia',
            'preschool_type',
            'whatsapp_contact',
            'email',
            'latitude',
            'longitude',
        ]

        labels = {
            'name': 'Naran Pre-Escolar',
            'municipality': 'Munisípiu',
            'administrative_post': 'Postu Administrativu',
            'suco': 'Suku',
            'aldeia': 'Aldeia',
            'preschool_type': 'Tipu Pre-Escolar',
            'whatsapp_contact': 'Kontaktu WhatsApp',
            'email': 'Email',
            'latitude': 'Latitude',
            'longitude': 'Longitude',
        }

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Hatama naran pre-escolar'
            }),

            'municipality': forms.Select(attrs={
                'class': 'form-select'
            }),

            'administrative_post': forms.Select(attrs={
                'class': 'form-select'
            }),

            'suco': forms.Select(attrs={
                'class': 'form-select'
            }),

            'aldeia': forms.Select(attrs={
                'class': 'form-select'
            }),

            'preschool_type': forms.Select(attrs={
                'class': 'form-select'
            }),

            'whatsapp_contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+670 7XXXXXXX'
            }),

            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'example@email.com'
            }),

            'latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '-8.5569'
            }),

            'longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '125.5603'
            }),
        }

    # ------------------------------------
    # DEPENDENT DROPDOWN LOGIC
    # ------------------------------------
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Municipality
        self.fields['municipality'].queryset = Municipality.objects.all()
        self.fields['municipality'].empty_label = "Selesiona Munisípiu"

        # Empty defaults
        self.fields['administrative_post'].queryset = AdministrativePost.objects.none()
        self.fields['suco'].queryset = Suco.objects.none()
        self.fields['aldeia'].queryset = Aldeia.objects.none()

        # Municipality → Administrative Post
        if 'municipality' in self.data:
            try:
                municipality_id = int(self.data.get('municipality'))

                self.fields['administrative_post'].queryset = (
                    AdministrativePost.objects.filter(
                        municipality_id=municipality_id
                    )
                )

            except (ValueError, TypeError):
                pass

        # Administrative Post → Suco
        if 'administrative_post' in self.data:
            try:
                post_id = int(self.data.get('administrative_post'))

                self.fields['suco'].queryset = (
                    Suco.objects.filter(
                        administrative_post_id=post_id
                    )
                )

            except (ValueError, TypeError):
                pass

        # Suco → Aldeia
        if 'suco' in self.data:
            try:
                suco_id = int(self.data.get('suco'))

                self.fields['aldeia'].queryset = (
                    Aldeia.objects.filter(
                        suco_id=suco_id
                    )
                )

            except (ValueError, TypeError):
                pass

        # Editing existing instance
        elif self.instance.pk:

            self.fields['administrative_post'].queryset = (
                AdministrativePost.objects.filter(
                    municipality=self.instance.municipality
                )
            )

            self.fields['suco'].queryset = (
                Suco.objects.filter(
                    administrative_post=self.instance.administrative_post
                )
            )

            self.fields['aldeia'].queryset = (
                Aldeia.objects.filter(
                    suco=self.instance.suco
                )
            )



class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = ['name', 'teacher', 'group']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Enter classroom name'
            }),
            'teacher': forms.Select(attrs={
                'class': 'form-select form-select-lg'
            }),
            'group': forms.Select(attrs={
                'class': 'form-select form-select-lg'
            }),
        }