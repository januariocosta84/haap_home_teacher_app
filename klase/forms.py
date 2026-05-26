from django import forms


class AddChildToClassForm(forms.Form):
    user_id = forms.CharField(
        max_length=30,
        label="Child Code (user_id)"
    )

    first_name = forms.CharField(
        max_length=50,
        label="Child First Name"
    )

class ChildCodeEnrollmentForm(forms.Form):
    child_code = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Child Code'
        })
    )


class ChildCodeEnrollmentForm(forms.Form):
    child_code = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Child Code (e.g. CHD-000123)',
            'autocomplete': 'off'
        })
    )

    def clean_child_code(self):
        code = self.cleaned_data['child_code'].strip().upper()

        if not code:
            raise forms.ValidationError("Child code is required.")

        return code