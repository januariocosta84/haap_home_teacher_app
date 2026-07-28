from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from core.forms import LoginForm
from core.audit import log_action
from preschools.models import Preschool, PreschoolTeacher
from klase.models import Classroom

User = get_user_model()

def _role_home(user):
    """Return the redirect URL name for a logged-in user's home dashboard."""
    role_map = {
        'moe_admin':            'core:moe_admin_dashboard',
        'moe_auditing':         'core:moe_admin_dashboard',
        'municipality_analyst': 'core:municipality_dashboard',
        'teacher':              'preschools:teacher_preschool_list',
        'parent':               'core:child_list',
    }
    return role_map.get(user.role, 'core:moe_admin_dashboard')


def user_login(request):
    if request.user.is_authenticated:
        return redirect(_role_home(request.user))

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            whatsapp_number = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=whatsapp_number, password=password)
            if user is not None:
                login(request, user)

                # Redirect based on role
                if user.role == "moe_admin":
                    return redirect("core:moe_admin_dashboard")
                elif user.role == "parent":
                    return redirect("core:child_list")
                elif user.role == "municipality_analyst":
                    return redirect("core:municipality_dashboard")
                elif user.role == "teacher":
                    # approved_relation = PreschoolTeacher.objects.filter(
                    #     teacher=user,
                    #     is_active=True,
                    #     is_approved=True
                    # ).select_related('preschool').first()

                    # if approved_relation:
                    #     return redirect(
                    #         "preschools:preschool_detail",
                    #         pk=approved_relation.preschool.id
                    #     )
                    return redirect("preschools:teacher_preschool_list")
                else:
                    messages.error(request, "Unknown role. Contact admin.")
                    return redirect("core:login")
            else:
                pending_user = User.objects.filter(
                    whatsapp_number=whatsapp_number,
                    role="teacher",
                    is_active=False
                ).first()

                if pending_user:
                    messages.error(
                        request,
                        "Registrasaun formadór iha status pendende. Favor espera MoE admin aprova."
                    )
                else:
                    messages.error(request, "Invalid WhatsApp number or password")
    else:
        form = LoginForm()
    return render(request, "users/login_file.html", {"form": form})


def user_logout(request):
    log_action(
        request=request,
        action='logout', module='Auth',
        description=f'{request.user.get_full_name() or request.user.username} logout.',
    )
    logout(request)
    return redirect("core:login")
