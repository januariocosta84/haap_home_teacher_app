# core/forms.py
import datetime
from django import forms
from django.core.validators import RegexValidator
from .models import ApkVersion, Child, User, Location
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
from django import forms
from django.core.validators import RegexValidator
from .models import User, Municipality, AdministrativePost, Suco, Aldeia
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model

#Registration form
class ParentRegistrationForm(forms.ModelForm):
    # WhatsApp format validation
    whatsapp_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Hakerek numeru whatsapp (e.g., +67077123456)."
    )
    whatsapp_number = forms.CharField(
        validators=[whatsapp_regex],
        max_length=15,
        label="WhatsApp Number",
        help_text="We'll send a verification link via WhatsApp."
    )

    # Location fields (cascading dropdowns)
    municipality = forms.ModelChoiceField(
        queryset=Municipality.objects.all(),
        empty_label="Select Municipality",
        label="Municipality"
    )
    administrative_post = forms.ModelChoiceField(
        queryset=AdministrativePost.objects.none(),
        empty_label="Select Administrative Post",
        required=True,
        label="Administrative Post"
    )
    suco = forms.ModelChoiceField(
        queryset=Suco.objects.none(),
        empty_label="Select Suco",
        required=True,
        label="Suco"
    )
    aldeia = forms.ModelChoiceField(
        queryset=Aldeia.objects.none(),
        empty_label="Select Aldeia",
        required=True,
        label="Aldeia"
    )

    # Optional email
    email = forms.EmailField(required=False, label="Email (Optional)")

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'address',
            'whatsapp_number', 'email',
            'municipality', 'administrative_post', 'suco', 'aldeia'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Always set role and is_verified
        self.instance.role = 'parent'
        self.instance.is_verified = False

        # Populate dropdowns dynamically based on form data
        if 'municipality' in self.data:
            try:
                municipality_id = int(self.data.get('municipality'))
                self.fields['administrative_post'].queryset = AdministrativePost.objects.filter(
                    municipality_id=municipality_id
                )
            except (ValueError, TypeError):
                pass

        if 'administrative_post' in self.data:
            try:
                ap_id = int(self.data.get('administrative_post'))
                self.fields['suco'].queryset = Suco.objects.filter(administrative_post_id=ap_id)
            except (ValueError, TypeError):
                pass

        if 'suco' in self.data:
            try:
                suco_id = int(self.data.get('suco'))
                self.fields['aldeia'].queryset = Aldeia.objects.filter(suco_id=suco_id)
            except (ValueError, TypeError):
                pass

        # If editing an existing instance → prepopulate related dropdowns
        elif self.instance.pk:
            if self.instance.municipality:
                self.fields['administrative_post'].queryset = AdministrativePost.objects.filter(
                    municipality=self.instance.municipality
                )
            if self.instance.administrative_post:
                self.fields['suco'].queryset = Suco.objects.filter(
                    administrative_post=self.instance.administrative_post
                )
            if self.instance.suco:
                self.fields['aldeia'].queryset = Aldeia.objects.filter(suco=self.instance.suco)

    def save(self, commit=True):
        user = super().save(commit=False)
        # Temp password can be generated if needed (e.g., random token)
        if commit:
            user.save()
        return user

#User login form 
class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="WhatsApp Number",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Hakerek numeru whatsapp '})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Hakerek password'})
    )

class ChildRegistrationForm(forms.ModelForm):
    class Meta:
        model = Child
        fields = ['first_name', 'year_of_birth']   # 👈 removed age_group
        labels = {
            'first_name': 'Naran Kompletu',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': "Oan nia naran Kompletu"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_year = datetime.date.today().year
        valid_years = [current_year - i for i in range(3, 7)]  # 3–6 years old
        self.fields['year_of_birth'] = forms.ChoiceField(
            choices=[(year, year) for year in valid_years],
            widget=forms.Select(attrs={'class': 'form-select'}),
            label="Tinan moris"
        )

    def clean(self):
        cleaned_data = super().clean()
        year_of_birth = cleaned_data.get('year_of_birth')

        if year_of_birth:
            year_of_birth = int(year_of_birth)
            current_year = datetime.date.today().year
            age = current_year - year_of_birth

            # Auto-assign age_group
            if 3 <= age <= 4:
                cleaned_data['age_group'] = 'A'
            elif 5 <= age <= 6:
                cleaned_data['age_group'] = 'B'
            else:
                raise forms.ValidationError("Child must be between 3–6 years old.")

        return cleaned_data

    def save(self, commit=True):
        child = super().save(commit=False)
        current_year = datetime.date.today().year
        age = current_year - int(self.cleaned_data['year_of_birth'])

        # Assign group before saving
        if 3 <= age <= 4:
            child.age_group = 'A'
        elif 5 <= age <= 6:
            child.age_group = 'B'

        if commit:
            child.save()
        return child

#Apk version form
class ApkVersionForm(forms.ModelForm):
    class Meta:
        model = ApkVersion
        fields = ['version_name', 'download_url', 'is_latest']
        widgets = {
            'version_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 1.0.3'}),
            'download_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com/app.apk'}),
            'is_latest': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
# User profile image update form
class ProfileImageForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['image']   # only handle image field
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control-file'})  # no clear checkbox
        }


# Profile edit form used by `profile_view`
class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'address', 'municipality', 'administrative_post', 'suco', 'aldeia']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Preload municipalities
        self.fields['municipality'].queryset = Municipality.objects.all()
        self.fields['municipality'].empty_label = "Selesiona Munisípiu"

        # Default empty for dependent fields
        self.fields['administrative_post'].queryset = AdministrativePost.objects.none()
        self.fields['suco'].queryset = Suco.objects.none()
        self.fields['aldeia'].queryset = Aldeia.objects.none()

        # If instance provided, pre-populate dependent dropdowns
        if self.instance and getattr(self.instance, 'municipality', None):
            self.fields['administrative_post'].queryset = AdministrativePost.objects.filter(municipality=self.instance.municipality)
        if self.instance and getattr(self.instance, 'administrative_post', None):
            self.fields['suco'].queryset = Suco.objects.filter(administrative_post=self.instance.administrative_post)
        if self.instance and getattr(self.instance, 'suco', None):
            self.fields['aldeia'].queryset = Aldeia.objects.filter(suco=self.instance.suco)

# class ParentRegisterForm(forms.ModelForm):
#     password = forms.CharField(
#         widget=forms.PasswordInput(attrs={"class": "form-control"})
#     )

#     class Meta:
#         model = User
#         fields = [
#             "first_name", "last_name", "whatsapp_number", "email", "address",
#             "municipality", "administrative_post", "suco", "aldeia", "password"
#         ]
#         widgets = {
#             "first_name": forms.TextInput(attrs={"class": "form-control"}),
#             "last_name": forms.TextInput(attrs={"class": "form-control"}),
#             "whatsapp_number": forms.TextInput(attrs={"class": "form-control"}),
#             "email": forms.EmailInput(attrs={"class": "form-control"}),
#             "address": forms.TextInput(attrs={"class": "form-control"}),

#             # ✅ Force dropdowns to use Bootstrap's "form-select"
#             "municipality": forms.Select(attrs={"class": "custom-select"}),
#             "administrative_post": forms.Select(attrs={"class": "custom-select"}),
#             "suco": forms.Select(attrs={"class": "custom-select"}),
#             "aldeia": forms.Select(attrs={"class": "custom-select"}),
#         }

#     def save(self, commit=True):
#         user = super().save(commit=False)
#         user.role = "parent"  # force parent role
#         user.username = self.cleaned_data["whatsapp_number"]  # use WhatsApp as username
#         user.set_password(self.cleaned_data["password"])  # hash password
#         if commit:
#             user.save()
#         return user
class ParentRegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

    class Meta:
        model = User
        fields = [
            "first_name", "last_name", "whatsapp_number", "email", "address",
            "municipality", "administrative_post", "suco", "aldeia", "password"
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "whatsapp_number": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),

            # Bootstrap 5 style for dropdowns
            "municipality": forms.Select(attrs={"class": "custom-select"}),
            "administrative_post": forms.Select(attrs={"class": "custom-select"}),
            "suco": forms.Select(attrs={"class": "custom-select"}),
            "aldeia": forms.Select(attrs={"class": "custom-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Preload municipalities
        self.fields['municipality'].queryset = Municipality.objects.all()
        self.fields['municipality'].empty_label = "Selesiona Munisípiu"

        # Default empty for dependent fields
        self.fields['administrative_post'].queryset = AdministrativePost.objects.none()
        self.fields['suco'].queryset = Suco.objects.none()
        self.fields['aldeia'].queryset = Aldeia.objects.none()

        # If POST data exists, filter dependent fields so selected value works
        if 'municipality' in self.data:
            try:
                municipality_id = int(self.data.get('municipality'))
                self.fields['administrative_post'].queryset = AdministrativePost.objects.filter(municipality_id=municipality_id)
            except (ValueError, TypeError):
                pass  # invalid input; ignore

        if 'administrative_post' in self.data:
            try:
                post_id = int(self.data.get('administrative_post'))
                self.fields['suco'].queryset = Suco.objects.filter(administrative_post_id=post_id)
            except (ValueError, TypeError):
                pass

        if 'suco' in self.data:
            try:
                suco_id = int(self.data.get('suco'))
                self.fields['aldeia'].queryset = Aldeia.objects.filter(suco_id=suco_id)
            except (ValueError, TypeError):
                pass


    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = "parent"  # force parent role
        user.username = self.cleaned_data["whatsapp_number"]  # use WhatsApp as username
        user.set_password(self.cleaned_data["password"])  # hash password
        if commit:
            user.save()
        return user


# Admin-facing minimal parent form (used for CRUD in `views/parents.py`)
class ParentForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'whatsapp_number', 'email', 'address',
            'municipality', 'administrative_post', 'suco', 'aldeia'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'whatsapp_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'municipality': forms.Select(attrs={'class': 'custom-select'}),
            'administrative_post': forms.Select(attrs={'class': 'custom-select'}),
            'suco': forms.Select(attrs={'class': 'custom-select'}),
            'aldeia': forms.Select(attrs={'class': 'custom-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['municipality'].queryset = Municipality.objects.all()
        self.fields['administrative_post'].queryset = AdministrativePost.objects.none()
        self.fields['suco'].queryset = Suco.objects.none()
        self.fields['aldeia'].queryset = Aldeia.objects.none()

        if 'municipality' in self.data:
            try:
                municipality_id = int(self.data.get('municipality'))
                self.fields['administrative_post'].queryset = AdministrativePost.objects.filter(municipality_id=municipality_id)
            except (ValueError, TypeError):
                pass

        if 'administrative_post' in self.data:
            try:
                post_id = int(self.data.get('administrative_post'))
                self.fields['suco'].queryset = Suco.objects.filter(administrative_post_id=post_id)
            except (ValueError, TypeError):
                pass

        if 'suco' in self.data:
            try:
                suco_id = int(self.data.get('suco'))
                self.fields['aldeia'].queryset = Aldeia.objects.filter(suco_id=suco_id)
            except (ValueError, TypeError):
                pass    
# Staff registration form (for municipality analysts and teachers)
class StaffRegisterForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "whatsapp_number", "email", "role"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].choices = [
            ("municipality_analyst", "Municipality Analyst"),
            ("teacher", "Teacher"),
        ]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["whatsapp_number"]  
        user.set_unusable_password()  # ✅ force password reset
        if commit:
            user.save()

            # Send reset password email
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = f"{settings.SITE_URL}{reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})}"

            subject = "Set your account password"
            message = f"""
            Hello {user.first_name},

            An account has been created for you in the system.

            Please click the link below to set your password:
            {reset_url}

            If you didn’t expect this, you can ignore the email.
            """
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

        return user


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Password (optional)"
        })
    )

    role = forms.ChoiceField(
        choices=[
            ("municipality_analyst", "Municipality Analyst"),
            ("teacher", "Teacher"),
            ("parent", "Parent"),
        ],
        widget=forms.Select(attrs={"class": "form-select"})
    )

    class Meta:
        model = User
        fields = [
            "first_name", "last_name", "whatsapp_number", "email", "address",
            "municipality", "administrative_post", "suco", "aldeia",
            "role", "password"
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "whatsapp_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "+67077123456"
            }),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),

            # Bootstrap select fields
            "municipality": forms.Select(attrs={"class": "form-select"}),
            "administrative_post": forms.Select(attrs={"class": "form-select"}),
            "suco": forms.Select(attrs={"class": "form-select"}),
            "aldeia": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Municipality dropdown
        self.fields["municipality"].queryset = Municipality.objects.all()
        self.fields["municipality"].empty_label = "Select Municipality"

        # Empty dependent dropdowns by default
        self.fields["administrative_post"].queryset = AdministrativePost.objects.none()
        self.fields["suco"].queryset = Suco.objects.none()
        self.fields["aldeia"].queryset = Aldeia.objects.none()

        # Handle cascading selects (POST / bound form)
        if self.is_bound:
            try:
                municipality_id = int(self.data.get("municipality", 0))
                self.fields["administrative_post"].queryset = (
                    AdministrativePost.objects.filter(municipality_id=municipality_id)
                )
            except (ValueError, TypeError):
                pass

            try:
                post_id = int(self.data.get("administrative_post", 0))
                self.fields["suco"].queryset = (
                    Suco.objects.filter(administrative_post_id=post_id)
                )
            except (ValueError, TypeError):
                pass

            try:
                suco_id = int(self.data.get("suco", 0))
                self.fields["aldeia"].queryset = (
                    Aldeia.objects.filter(suco_id=suco_id)
                )
            except (ValueError, TypeError):
                pass

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["whatsapp_number"]

        if self.cleaned_data.get("password"):
            user.set_password(self.cleaned_data["password"])
        else:
            user.set_unusable_password()

        if commit:
            user.save()
        return user


# Simple admin user form used by `user_management` views
class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'whatsapp_number', 'email', 'address', 'municipality', 'administrative_post', 'suco', 'aldeia', 'role'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['municipality'].queryset = Municipality.objects.all()
        self.fields['administrative_post'].queryset = AdministrativePost.objects.none()
        self.fields['suco'].queryset = Suco.objects.none()
        self.fields['aldeia'].queryset = Aldeia.objects.none()

        if 'municipality' in self.data:
            try:
                municipality_id = int(self.data.get('municipality'))
                self.fields['administrative_post'].queryset = AdministrativePost.objects.filter(municipality_id=municipality_id)
            except (ValueError, TypeError):
                pass

        if 'administrative_post' in self.data:
            try:
                post_id = int(self.data.get('administrative_post'))
                self.fields['suco'].queryset = Suco.objects.filter(administrative_post_id=post_id)
            except (ValueError, TypeError):
                pass

        if 'suco' in self.data:
            try:
                suco_id = int(self.data.get('suco'))
                self.fields['aldeia'].queryset = Aldeia.objects.filter(suco_id=suco_id)
            except (ValueError, TypeError):
                pass


        # Apply Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({"class": "form-select"})
            elif isinstance(field.widget, forms.PasswordInput):
                field.widget.attrs.update({"class": "form-control", "placeholder": "Enter password (optional)"})
            else:
                field.widget.attrs.update({"class": "form-control"})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["whatsapp_number"]
        if self.cleaned_data["password"]:
            user.set_password(self.cleaned_data["password"])
        else:
            user.set_unusable_password()  # must use reset link
        if commit:
            user.save()
        return user
