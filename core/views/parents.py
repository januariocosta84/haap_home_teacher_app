from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views import View
from core.forms import ParentForm, ParentRegisterForm, ParentRegistrationForm
from core.models import User

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


class ParentRegisterView(View):
    def get(self, request):
        form = ParentRegisterForm()
        return render(request, "registration/parent_register.html", {"form": form})

    def post(self, request):
        form = ParentRegisterForm(request.POST)
        if form.is_valid():
            form.save()

            # ✅ ADD THIS LINE
            messages.success(request, f"Konta {form.cleaned_data['first_name']} kria ho susesu!")

            return redirect("core:login")

        return render(request, "registration/parent_register.html", {"form": form})