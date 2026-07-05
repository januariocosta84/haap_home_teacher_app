from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView
from core.models import ApkVersion
from core.forms import ApkVersionForm


def download_apk(request, apk_id):
    apk = get_object_or_404(ApkVersion, id=apk_id)
    download_url = apk.get_download_url()
    if not download_url:
        messages.error(request, "Download APK seidauk disponivel.")
        return redirect("core:apk_list")
    return redirect(download_url)


@login_required
def upload_apk(request):
    if request.user.role != "moe_admin":
        messages.error(request, "Ita la iha permisaun atu upload APK.")
        return redirect("core:apk_list")

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
    if request.user.role != "moe_admin":
        messages.error(request, "Ita la iha permisaun atu altera APK.")
        return redirect("core:apk_list")

    apk = get_object_or_404(ApkVersion, id=apk_id)
    if request.method == 'POST':
        form = ApkVersionForm(request.POST, request.FILES, instance=apk)
        if form.is_valid():
            form.save()
            messages.success(request, "APK version updated successfully.")
            return redirect('core:apk_list')
    else:
        form = ApkVersionForm(instance=apk)
    return render(request, 'apk/edit_apk.html', {'form': form, 'apk': apk})


@login_required
def apk_list(request):
    apks = ApkVersion.objects.order_by('-released_at')
    latest = apks.filter(is_latest=True).first()
    return render(request, 'apk/apk_list.html', {
        'apks': apks,
        'latest': latest,
        'user': request.user,
    })


class LatestApkView(ListView):
    model = ApkVersion
    template_name = "apk/latest_version.html"
    context_object_name = "versions"

    def get_queryset(self):
        return ApkVersion.objects.filter(is_latest=True).order_by("-released_at")
