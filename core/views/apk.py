from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from core.models import ApkVersion, AppNotification, User
from core.forms import ApkVersionForm
from core.audit import log_action


def _purge_apk_files(exclude_pk=None):
    """Delete physical APK files from storage for all records (except exclude_pk).

    Also clears the apk_file DB field on affected records so stale URLs
    are not served from the version list.  Finally, unconditionally removes
    the canonical haap_uma.apk path so orphaned files (no DB record) never
    block future uploads.
    """
    from django.core.files.storage import default_storage
    qs = ApkVersion.objects.all()
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    pks_cleared = []
    for apk in qs:
        if apk.apk_file:
            storage, name = apk.apk_file.storage, apk.apk_file.name
            if storage.exists(name):
                storage.delete(name)
            pks_cleared.append(apk.pk)
    if pks_cleared:
        ApkVersion.objects.filter(pk__in=pks_cleared).update(apk_file=None)
    # Remove the fixed-name file regardless of DB state so orphaned files
    # (e.g. created by a script running as root) never shadow new uploads.
    if default_storage.exists('apk/haap_uma.apk'):
        default_storage.delete('apk/haap_uma.apk')


@login_required
def download_apk(request, apk_id):
    # moe_admin manages APKs; parents/teachers may download; others are blocked
    if request.user.role not in ('moe_admin', 'parent', 'teacher'):
        return redirect('core:login')
    apk = get_object_or_404(ApkVersion, id=apk_id)
    download_url = apk.get_download_url()
    if not download_url:
        messages.error(request, "Download APK seidauk disponivel.")
        return redirect("core:login")
    log_action(
        request=request,
        action='download', module='APK',
        description=f'{request.user.get_full_name()} download APK versaun {apk.version_name}.',
        record_id=str(apk.id),
        record_name=apk.version_name,
    )
    return redirect(download_url)


@login_required
def upload_apk(request):
    if request.user.role != "moe_admin":
        messages.error(request, "Ita la iha permisaun atu upload APK.")
        return redirect("core:apk_list")

    if request.method == 'POST':
        form = ApkVersionForm(request.POST, request.FILES)
        if form.is_valid():
            has_new_file = bool(request.FILES.get('apk_file'))
            try:
                if has_new_file:
                    _purge_apk_files()
                new_apk = form.save()
                if has_new_file:
                    _notify_parents_apk_update(new_apk)
                log_action(
                    request=request,
                    action='upload', module='APK',
                    description=f"Upload APK versaun {new_apk.version_name}",
                    record_id=str(new_apk.id),
                    record_name=f"HAAP v{new_apk.version_name}",
                    new_value={'version': new_apk.version_name, 'is_latest': new_apk.is_latest},
                )
                messages.success(
                    request,
                    f"APK versaun {new_apk.version_name} karga ho susesu!"
                    + (" Pais sira hetan notifikasaun ona." if has_new_file else ""),
                )
                return JsonResponse({"success": True})
            except Exception as exc:
                import traceback, logging
                logging.getLogger(__name__).error(
                    "APK upload failed: %s\n%s", exc, traceback.format_exc()
                )
                return JsonResponse(
                    {"success": False, "errors": {"__all__": [str(exc)]}},
                    status=500,
                )
        return JsonResponse({"success": False, "errors": form.errors})

    form = ApkVersionForm()
    return render(request, 'apk/upload_apk.html', {'form': form})


@login_required
@require_POST
def delete_apk(request, apk_id):
    if request.user.role != "moe_admin":
        return JsonResponse({'ok': False, 'error': 'Permisaun la iha.'}, status=403)
    apk = get_object_or_404(ApkVersion, id=apk_id)
    version = apk.version_name
    apk_id_str = str(apk.id)
    apk.delete()
    log_action(
        request=request,
        action='delete', module='APK',
        description=f"Apaga APK versaun {version}",
        record_id=apk_id_str,
        record_name=f"HAAP v{version}",
    )
    return JsonResponse({'ok': True, 'message': f'APK v{version} apagadu ho susesu.'})


@login_required
def edit_apk(request, apk_id):
    if request.user.role != "moe_admin":
        messages.error(request, "Ita la iha permisaun atu altera APK.")
        return redirect("core:apk_list")

    apk = get_object_or_404(ApkVersion, id=apk_id)
    if request.method == 'POST':
        form = ApkVersionForm(request.POST, request.FILES, instance=apk)
        if form.is_valid():
            old_version = apk.version_name
            if request.FILES.get('apk_file'):
                _purge_apk_files(exclude_pk=apk.pk)
            updated = form.save()
            log_action(
                request=request,
                action='update', module='APK',
                description=f"Atualiza APK versaun {updated.version_name}",
                record_id=str(updated.id),
                record_name=f"HAAP v{updated.version_name}",
                previous_value={'version': old_version},
                new_value={'version': updated.version_name, 'is_latest': updated.is_latest},
            )
            messages.success(request, "Versaun APK atualiza ho susesu.")
            return redirect('core:apk_list')
    else:
        form = ApkVersionForm(instance=apk)
    return render(request, 'apk/edit_apk.html', {'form': form, 'apk': apk})


@login_required
def apk_list(request):
    # moe_admin: full management; parent: download-only (template hides admin buttons)
    if request.user.role not in ('moe_admin', 'parent'):
        return redirect('core:login')
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


# ── APK update notification helpers ──────────────────────────────────────────

def _notify_parents_apk_update(apk):
    """Create an AppNotification for every active parent about a new APK file."""
    parents = User.objects.filter(role='parent', is_active=True)
    AppNotification.objects.bulk_create([
        AppNotification(
            recipient=p,
            notification_type='apk_update',
            title='Aplikasaun Foun Disponivel',
            message=f'Versaun foun HAAP v{apk.version_name} ona disponivel. '
                    f'Baixa agora atu hetan funsaun sira ikus.',
            action_url='/apk/download-latest/',
        )
        for p in parents
    ])


# ── Parent APK notification API endpoints ────────────────────────────────────

@login_required
def apk_notif_count(request):
    count = AppNotification.objects.filter(
        recipient=request.user, is_read=False
    ).count()
    return JsonResponse({'count': count})


@login_required
def apk_notif_list(request):
    notifs = (
        AppNotification.objects
        .filter(recipient=request.user)
        .order_by('-created_at')[:20]
    )
    data = [
        {
            'id': str(n.id),
            'type': n.notification_type,
            'title': n.title,
            'message': n.message,
            'action_url': n.action_url,
            'is_read': n.is_read,
            'created_at': n.created_at.strftime('%d/%m/%Y %H:%M'),
        }
        for n in notifs
    ]
    return JsonResponse({'notifications': data})


@login_required
@require_POST
def apk_notif_mark_read(request, notif_id):
    n = get_object_or_404(AppNotification, id=notif_id, recipient=request.user)
    n.is_read = True
    n.save(update_fields=['is_read'])
    return JsonResponse({'ok': True})


@login_required
@require_POST
def apk_notif_mark_all_read(request):
    AppNotification.objects.filter(
        recipient=request.user, is_read=False
    ).update(is_read=True)
    return JsonResponse({'ok': True})
