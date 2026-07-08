import os
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.contrib import messages
from core.forms import ProfileForm, ProfileImageForm, ChangePasswordForm
from core.audit import log_action

DEFAULT_PROFILE_IMAGE = "apk/user.jpg"

@login_required
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil atualiza ho susesu.")
            return redirect('core:profile')
    else:
        form = ProfileForm(instance=user)
    return render(request, 'users/profile.html', {'form': form})


@login_required
def update_profile_image(request):
    if request.method == "POST":
        form = ProfileImageForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            old_image = request.user.image
            old_path = None
            if old_image and old_image.name and old_image.name != DEFAULT_PROFILE_IMAGE:
                try:
                    old_path = old_image.path
                except Exception:
                    old_path = None
            form.save()
            if old_path and os.path.isfile(old_path):
                os.remove(old_path)
            messages.success(request, "Perfil foto atualiza ho susesu.")
            return redirect('core:profile')
    else:
        form = ProfileImageForm(instance=request.user)
    return render(request, "users/update_profile_image.html", {"form": form})


@login_required
def change_password(request):
    """Allow user to change their password"""
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            user = request.user
            current_password = form.cleaned_data.get('current_password')
            new_password = form.cleaned_data.get('new_password')
            
            # Verify current password
            if not user.check_password(current_password):
                messages.error(request, "Password atual la loos.")
                return redirect('core:password_change')
            
            # Set new password
            user.set_password(new_password)
            user.save()
            log_action(
                request=request,
                action='password_change', module='Profile',
                description=f"{user.get_full_name()} muda password.",
                record_id=str(user.id),
                record_name=user.get_full_name(),
            )
            messages.success(request, "Password changed successfully. Please login again.")
            return redirect('core:login')
    else:
        form = ChangePasswordForm()
    
    return render(request, 'users/change_password.html', {'form': form})
