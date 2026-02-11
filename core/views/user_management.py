from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views import View
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model

from core.forms import UserForm, UserRegistrationForm
from core.models import Child

User = get_user_model()


class UserManagementView(View):
    def get(self, request):
        # Only MoE admins can access user management
        if not request.user.is_authenticated or request.user.role != "moe_admin":
            messages.error(request, "Aksesu negadu.")
            return redirect("core:home")

        # Query users by role
        parents = User.objects.filter(role="parent")
        teachers = User.objects.filter(role="teacher")
        analysts = User.objects.filter(role="municipality_analyst")
        admins = User.objects.filter(role="moe_admin")

        context = {
            "parents": parents,
            "teachers": teachers,
            "analysts": analysts,
            "admins": admins,
            "children": Child.objects.all(),
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
    """Edit an existing user (MoE admin only)."""
    if request.user.role != "moe_admin":
        messages.error(request, "Aksesu negadu.")
        return redirect("core:user_management")

    user_obj = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        form = UserRegistrationForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "User updated successfully.")
            return redirect("core:user_management")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserRegistrationForm(instance=user_obj)

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
