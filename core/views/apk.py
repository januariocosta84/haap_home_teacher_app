from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView
from core.models import ApkVersion
from core.forms import ApkVersionForm


def download_apk(request, apk_id):
    """Redirect to the APK's configured download URL.

    We no longer store an APK file object in the DB; `ApkVersion` has
    a `download_url` (external or S3) which we redirect users to.
    """
    apk = get_object_or_404(ApkVersion, id=apk_id)
    return redirect(apk.download_url)


@login_required
def upload_apk(request):
    apk = ApkVersion.objects.first()  # 🔥 only one record
    if request.method == 'POST':
        form = ApkVersionForm(request.POST, request.FILES, instance=apk)
        if form.is_valid():
            form.save()
            return JsonResponse({"success": True})
        return JsonResponse({"success": False, "errors": form.errors})

    form = ApkVersionForm()
    return render(request, 'apk/upload_apk.html', {'form': form})


@login_required
def edit_apk(request, apk_id):
    apk = get_object_or_404(ApkVersion, id=apk_id)
    if request.method == 'POST':
        form = ApkVersionForm(request.POST, request.FILES, instance=apk)
        if form.is_valid():
            form.save()
            messages.success(request, "APK version updated successfully.")
            return redirect('apk_list')
    else:
        form = ApkVersionForm(instance=apk)
    return render(request, 'apk/edit_apk.html', {'form': form, 'apk': apk})


@login_required
def apk_list(request):
    user = request.user
    print(f"User {user.username} accessed the APK list." f"Is staff: {user.is_staff}, Is superuser: {user.is_superuser}","Role: {user.role}",user.role)
    apks = ApkVersion.objects.order_by('-released_at')
    return render(request, 'apk/apk_list.html', {'apks': apks, 'user': user})


class LatestApkView(ListView):
    model = ApkVersion
    template_name = "apk/latest_version.html"
    context_object_name = "versions"

    def get_queryset(self):
        return ApkVersion.objects.filter(is_latest=True).order_by("-released_at")
