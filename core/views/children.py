from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from core.forms import ChildRegistrationForm
from core.models import Child
from core.audit import log_action

@login_required
def children_list(request):
    children = Child.objects.filter(parent=request.user).order_by('-created_at')
    return render(request, 'core/children_list.html', {'children': children})

@login_required
def child_registration(request):
    if request.method == 'POST':
        form = ChildRegistrationForm(request.POST)
        if form.is_valid():
            child = form.save(commit=False)
            child.parent = request.user
            child.save()
            log_action(
                request=request,
                user=request.user,
                action='create',
                module='children',
                description=f"Rejistu labarik '{child.first_name}' (kódigu: {child.user_id}) husi inan-aman.",
                record_id=str(child.id),
                record_name=child.first_name,
            )
            messages.success(
                request,
                f"Labarik '{child.first_name}' rejistu ho susesu. Kodigu nia: {child.user_id}"
            )
            return redirect('core:child_list')
    else:
        form = ChildRegistrationForm()
    return render(request,'core/child_registration.html', {'form': form})

@login_required
def edit_child(request, child_id):
    child = get_object_or_404(Child, id=child_id, parent=request.user)
    if request.method == 'POST':
        form = ChildRegistrationForm(request.POST, instance=child)
        if form.is_valid():
            old_name = child.first_name
            form.save()
            log_action(
                request=request,
                user=request.user,
                action='update',
                module='children',
                description=f"Atualiza dadus labarik '{old_name}' → '{child.first_name}' (kódigu: {child.user_id}).",
                record_id=str(child.id),
                record_name=child.first_name,
            )
            messages.success(request, f"Labarik '{child.first_name}' aktualiza ho susesu.")
            return redirect('core:child_list')
    else:
        form = ChildRegistrationForm(instance=child)
    return render(request, 'core/edit_child.html', {'form': form, 'child': child})

@login_required
def delete_child(request, child_id):
    child = get_object_or_404(Child, id=child_id, parent=request.user)
    if request.method == 'POST':
        name = child.first_name
        child_id_str = str(child.id)
        user_id = child.user_id
        child.delete()
        log_action(
            request=request,
            user=request.user,
            action='delete',
            module='children',
            description=f"Hasai labarik '{name}' (kódigu: {user_id}) husi sistema.",
            record_id=child_id_str,
            record_name=name,
        )
        messages.warning(request, f"Child '{name}' has been deleted.")
        return redirect('core:child_list')
    return render(request, 'core/delete_child.html', {'child': child})
