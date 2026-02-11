from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from core.forms import LoginForm

def user_login(request):
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
                    return redirect("core:children_list")
                elif user.role == "municipality_analyst":
                    return redirect("core:municipality_dashboard")
                elif user.role == "teacher":
                    return redirect("core:teacher_dashboard")
                else:
                    messages.error(request, "Unknown role. Contact admin.")
                    return redirect("core:login")
            else:
                messages.error(request, "Invalid WhatsApp number or password")
    else:
        form = LoginForm()
    return render(request, "users/login_file.html", {"form": form})


def user_logout(request):
    logout(request)
    return redirect("core:login")
