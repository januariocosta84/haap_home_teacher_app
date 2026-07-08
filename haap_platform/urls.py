from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

handler404 = 'core.views.custom_404'


@login_required
def root_redirect(request):
    role = request.user.role
    if role == 'moe_admin':
        return redirect('core:moe_admin_dashboard')
    elif role == 'parent':
        return redirect('core:child_list')
    elif role == 'teacher':
        return redirect('preschools:teacher_preschool_list')
    elif role == 'municipality_analyst':
        return redirect('core:municipality_dashboard')
    return redirect('core:login')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', root_redirect, name='root_redirect'),

    path('', include(('core.urls', 'core'), namespace='core')),
    path('preschool/', include(('preschools.urls', 'preschools'), namespace='preschools')),
    path('equipment/', include(('equipment.urls', 'equipment'), namespace='equipment')),
    path('classroom/', include(('klase.urls', 'klase'), namespace='klase')),
    path('ticket/', include(('ticket.urls', 'ticket'), namespace='ticket')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
