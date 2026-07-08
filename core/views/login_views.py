from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from core.forms import LoginForm

def user_login(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            whatsapp_number = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=whatsapp_number, password=password)
            if user:
                login(request, user)
                # redirect based on role
                if user.role == "moe_admin":
                    return redirect("moe_admin_dashboard")
                elif user.role == "parent":
                    return redirect("core:child_list")
                elif user.role == "teacher":
                    return redirect("teacher_dashboard")
                elif user.role == "municipality_analyst":
                    return redirect("municipality_dashboard")
                else:
                    messages.error(request, "Unknown role. Contact admin.")
                    return redirect("login")
            else:
                messages.error(request, "Numeru telefone ka palavras passe laos diak")
        else:
            # Form validation failed - add custom error message
            messages.error(request, "Numeru telefone ka palavras passe laos diak")
    else:
        form = LoginForm()
    return render(request, "users/login_file.html", {"form": form})

@login_required
def user_logout(request):
    logout(request)
    return redirect("login")
