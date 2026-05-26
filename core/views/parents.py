import random

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views import View
from core.forms import ParentForm, ParentRegisterForm, ParentRegistrationForm, TeacherRegistrationForm
from core.models import User
from core.views.user_management import send_whatsapp_otp
from django.core.cache import cache as django_cache

@login_required
def parents_list(request):
    parents = User.objects.filter(role='parent')
    return render(request, 'core/parents_list.html', {'parents': parents})

@login_required
def add_parent(request):
    if request.method == 'POST':
        form = ParentForm(request.POST)
        if form.is_valid():
            parent = form.save(commit=False)
            parent.role = 'parent'
            parent.save()
            messages.success(request, f"Parent '{parent.first_name}' successfully added.")
            return redirect('parents_list')
    else:
        form = ParentForm()
    return render(request, 'core/add_parent.html', {'form': form})

@login_required
def edit_parent(request, parent_id):
    parent = get_object_or_404(User, id=parent_id, role='parent')
    if request.method == 'POST':
        form = ParentForm(request.POST, instance=parent)
        if form.is_valid():
            form.save()
            messages.success(request, f"Parent '{parent.first_name}' successfully updated.")
            return redirect('parents_list')
    else:
        form = ParentForm(instance=parent)
    return render(request, 'core/edit_parent.html', {'form': form, 'parent': parent})

@login_required
def delete_parent(request, parent_id):
    parent = get_object_or_404(User, id=parent_id, role='parent')
    if request.method == 'POST':
        name = parent.first_name
        parent.delete()
        messages.warning(request, f"Parent '{name}' has been deleted.")
        return redirect('parents_list')
    return render(request, 'core/delete_parent.html', {'parent': parent})


# Public-facing parent registration (two forms supported for backwards compatibility)
def parent_register(request):
    if request.method == 'POST':
        form = ParentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            messages.success(request, f"Thank you! A verification link has been sent to {user.whatsapp_number} via WhatsApp.")
            return redirect('core:parent_register')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ParentRegistrationForm()
    return render(request, 'core/parent_register.html', {'form': form})

##Kode ida ne registu parent la ho OTP, mas ho form ne suporta registu normal. Se iha tempu, sei remove form ne.
# class ParentRegisterView(View):
#     def get(self, request):
#         form = ParentRegisterForm()
#         return render(request, "registration/parent_register.html", {"form": form})

#     def post(self, request):
#         form = ParentRegisterForm(request.POST)
#         if form.is_valid():
#             form.save()

#             # ✅ ADD THIS LINE
#             messages.success(request, f"Konta {form.cleaned_data['first_name']} kria ho susesu!")

#             return redirect("core:login")

#         return render(request, "registration/parent_register.html", {"form": form})


##Code ida ne registu parent ho OTP, mas ho form ne suporta registu normal. Se iha tempu, sei remove form ne.
class ParentRegisterView(View):

    def get(self, request):
        form = ParentRegisterForm()

        return render(
            request,
            "registration/parent_register.html",
            {"form": form}
        )

    def post(self, request):

        form = ParentRegisterForm(request.POST)

        if form.is_valid():

            whatsapp_number = form.cleaned_data['whatsapp_number']

            # Check existing number
            if User.objects.filter(
                whatsapp_number=whatsapp_number
            ).exists():

                messages.error(
                    request,
                    "Numeru WhatsApp rejistadu ona."
                )

                return render(
                    request,
                    "registration/parent_register.html",
                    {"form": form}
                )

            # Generate OTP
            otp = str(random.randint(100000, 999999))

            # Cache keys
            cache_key = f"register_otp_{whatsapp_number}"
            attempt_key = f"register_attempts_{whatsapp_number}"

            # Save OTP
            django_cache.set(cache_key, otp, timeout=600)

            # Reset attempts
            django_cache.set(attempt_key, 0, timeout=600)

            # Save registration data temporarily
            request.session['register_data'] = request.POST.dict()
            request.session['register_whatsapp'] = whatsapp_number

            # Send OTP
            try:
                send_whatsapp_otp(
                    whatsapp_number,
                    otp
                )

            except Exception:

                messages.error(
                    request,
                    "Labele haruka OTP."
                )

                return render(
                    request,
                    "registration/parent_register.html",
                    {"form": form}
                )

            messages.success(
                request,
                "OTP haruka ona ba WhatsApp."
            )

            return redirect(
                'core:verify_register_otp'
            )

        return render(
            request,
            "registration/parent_register.html",
            {"form": form}
        )



class TeacherRegisterView(View):

    def get(self, request):
        form = TeacherRegistrationForm()
        return render(
            request,
            "registration/teacher_register.html",
            {"form": form}
        )

    def post(self, request):
        form = TeacherRegistrationForm(request.POST)

        if form.is_valid():
            whatsapp_number = form.cleaned_data['whatsapp_number']

            if User.objects.filter(
                whatsapp_number=whatsapp_number
            ).exists():
                messages.error(
                    request,
                    "Numeru WhatsApp rejistadu ona."
                )
                return render(
                    request,
                    "registration/teacher_register.html",
                    {"form": form}
                )

            form.save()
            messages.success(
                request,
                "Registrasaun formadór pendente. Favor espera MoE admin aprova."
            )
            return redirect('core:login')

        messages.error(request, "Favor korije erros sira iha fomulariu.")
        return render(
            request,
            "registration/teacher_register.html",
            {"form": form}
        )


MAX_OTP_ATTEMPTS = 3
def verify_register_otp(request):

    whatsapp_number = request.session.get(
        'register_whatsapp'
    )

    register_data = request.session.get(
        'register_data'
    )

    if not whatsapp_number or not register_data:

        messages.error(
            request,
            "Sesaun expirou."
        )

        return redirect(
            'core:parent_register'
        )

    cache_key = f"register_otp_{whatsapp_number}"
    attempt_key = f"register_attempts_{whatsapp_number}"

    saved_otp = django_cache.get(cache_key)

    attempts = django_cache.get(
        attempt_key,
        0
    )

    if request.method == 'POST':

        entered_otp = request.POST.get(
            'otp',
            ''
        ).strip()

        # OTP expired
        if not saved_otp:

            messages.error(
                request,
                "OTP expirou."
            )

            return redirect(
                'core:parent_register'
            )

        # Too many attempts
        if attempts >= MAX_OTP_ATTEMPTS:

            django_cache.delete(cache_key)
            django_cache.delete(attempt_key)

            messages.error(
                request,
                "Too many attempts."
            )

            return redirect(
                'core:parent_register'
            )

        # Wrong OTP
        if entered_otp != saved_otp:

            django_cache.set(
                attempt_key,
                attempts + 1,
                timeout=600
            )

            messages.error(
                request,
                "OTP sala."
            )

            return render(
                request,
                'registration/verify_register_otp.html'
            )

        # SUCCESS
        django_cache.delete(cache_key)
        django_cache.delete(attempt_key)

        form = ParentRegisterForm(register_data)

        if form.is_valid():

            form.save()

        # cleanup session
        request.session.pop(
            'register_whatsapp',
            None
        )

        request.session.pop(
            'register_data',
            None
        )

        messages.success(
            request,
            f"Konta {form.cleaned_data['first_name']} kria ho susesu!"
        )

        return redirect(
            'core:login'
        )

    return render(
        request,
        'registration/verify_register_otp.html'
    )