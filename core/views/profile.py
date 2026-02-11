from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from core.forms import ProfileForm, ProfileImageForm

@login_required
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile successfully updated.")
            return redirect('core:profile')
    else:
        form = ProfileForm(instance=user)
    return render(request, 'users/profile.html', {'form': form})


@login_required
def update_profile_image(request):
    if request.method == "POST":
        form = ProfileImageForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile image updated.")
            return redirect('core:profile')
    else:
        form = ProfileImageForm(instance=request.user)
    return render(request, "users/update_profile_image.html", {"form": form})
