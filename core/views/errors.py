from django.shortcuts import render
from django.urls import reverse


def custom_404(request, exception):
    user = request.user
    if user.is_authenticated:
        role = getattr(user, 'role', '')
        if role == 'moe_admin':
            redirect_url = reverse('core:moe_admin_dashboard')
        elif role == 'parent':
            redirect_url = reverse('core:child_list')
        elif role == 'municipality_analyst':
            redirect_url = reverse('core:municipality_dashboard')
        elif role == 'teacher':
            redirect_url = reverse('preschools:teacher_preschool_list')
        elif role == 'moe_auditing':
            redirect_url = reverse('core:auditing_dashboard')
        else:
            redirect_url = reverse('core:login')
    else:
        redirect_url = reverse('core:login')

    return render(request, '404.html', {'redirect_url': redirect_url}, status=404)