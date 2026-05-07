from functools import cache
import random

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views import View
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model

from core.forms import ForgotPasswordForm, ResetPasswordForm, UserForm, UserRegistrationForm, UserEditForm
# Make sure this is at the top of your views file
from django.core.cache import cache as django_cache
from core.models import Child

User = get_user_model()


class UserManagementView(View):
    def get(self, request):
        # Only MoE admins can access user management
        if not request.user.is_authenticated or request.user.role != "moe_admin":
            messages.error(request, "Aksesu negadu.")
            return redirect("core:children_list")

        # Query users by role
        parents = User.objects.filter(role="parent").order_by('-created_at')
        teachers = User.objects.filter(role="teacher")
        analysts = User.objects.filter(role="municipality_analyst")
        admins = User.objects.filter(role="moe_admin")

        context = {
            "parents": parents,
            "teachers": teachers,
            "analysts": analysts,
            "admins": admins,
            "children": Child.objects.all().order_by('-created_at'),
        }
        return render(request, "users/user_management.html", context)


@login_required
def register_user(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"User {user.first_name} created successfully and password setup email sent.")
            return redirect("core:moe_admin_dashboard")
    else:
        form = UserRegistrationForm()

    return render(request, "users/register_user.html", {"form": form})


@login_required
def view_user(request, user_id):
    """Simple view for a single user (MoE admin only)."""
    if request.user.role != "moe_admin":
        messages.error(request, "Aksesu negadu.")
        return redirect("core:user_management")

    user = get_object_or_404(User, id=user_id)
    return render(request, "users/view_user.html", {"obj": user})


@login_required
def edit_user(request, user_id):
    """Edit an existing user. MoE admins can edit anyone, other users can edit themselves."""
    user_obj = get_object_or_404(User, id=user_id)
    
    # Permission check: only moe_admin can edit other users, each user can edit themselves
    if request.user.role != "moe_admin" and request.user.id != user_obj.id:
        messages.error(request, "Aksesu negadu.")
        return redirect("core:user_management")

    if request.method == "POST":
        form = UserEditForm(request.POST, instance=user_obj, current_user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Utilizador atualizado ho sucesso.")
            # Redirect based on user role
            if request.user.role == "moe_admin":
                return redirect("core:user_management")
            else:
                # Regular users redirect to their profile page
                return redirect("core:profile")
        else:
            messages.error(request, "Favor corrija erros sira tuir mai.")
    else:
        form = UserEditForm(instance=user_obj, current_user=request.user)

    return render(request, "users/edit_user.html", {"form": form, "user_obj": user_obj})


@login_required
def delete_user(request, user_id):
    """Delete a user (MoE admin only). Shows confirmation form on GET, deletes on POST."""
    if request.user.role != "moe_admin":
        messages.error(request, "Aksesu negadu.")
        return redirect("core:user_management")

    user_obj = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        name = f"{user_obj.first_name} {user_obj.last_name}"
        user_obj.delete()
        messages.warning(request, f"User '{name}' has been deleted.")
        return redirect("core:user_management")

    return render(request, "users/confirm_delete_user.html", {"user_obj": user_obj})


# Backwards-compatible wrappers expected by other URL modules
@login_required
def user_list(request):
    # Keep legacy route working by redirecting to the unified management view
    return redirect('core:user_management')


@login_required
def add_user(request):
    # Use same behavior as `register_user` to avoid duplication
    return register_user(request)



def forgot_password(request):
    form = ForgotPasswordForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        whatsapp_number = form.cleaned_data['whatsapp_number']

        # Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))

        # Store OTP in cache for 10 minutes
        cache_key = f"reset_otp_{whatsapp_number}"
        django_cache.set(cache_key, otp, timeout=600)  # ← changed

        request.session['reset_whatsapp'] = whatsapp_number

        print(f"OTP for {whatsapp_number}: {otp}")

        messages.success(request, f"OTP haruka ona ba {whatsapp_number}. Validu minutu 10.")
        return redirect('core:verify_otp')

    return render(request, 'registration/forgot_password.html', {'form': form})


def verify_otp(request):
    whatsapp_number = request.session.get('reset_whatsapp')

    if not whatsapp_number:
        messages.error(request, "Sesaun expirou. Tenta fali.")
        return redirect('forgot_password')

    if request.method == 'POST':
        entered_otp = request.POST.get('otp', '').strip()
        cache_key = f"reset_otp_{whatsapp_number}"
        saved_otp = django_cache.get(cache_key)  # ← changed

        if not saved_otp:
            messages.error(request, "OTP expirou. Husu fali.")
            return redirect('core:forgot_password')

        if entered_otp != saved_otp:
            messages.error(request, "OTP sala. Tenta fali.")
            return render(request, 'registration/verify_otp.html')

        django_cache.delete(cache_key)  # ← changed
        request.session['otp_verified'] = True
        return redirect('core:reset_password')

    return render(request, 'registration/verify_otp.html')

def reset_password(request):
    whatsapp_number = request.session.get('reset_whatsapp')
    otp_verified = request.session.get('otp_verified')

    if not whatsapp_number or not otp_verified:
        messages.error(request, "Sesaun expirou. Tenta fali.")
        return redirect('core:forgot_password')

    form = ResetPasswordForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = User.objects.get(whatsapp_number=whatsapp_number)
        user.set_password(form.cleaned_data['new_password'])
        user.save()

        # Clear session
        del request.session['reset_whatsapp']
        del request.session['otp_verified']

        messages.success(request, "Password muda ona! Favor login fali.")
        return redirect('core:login')

    return render(request, 'registration/reset_password.html', {'form': form})