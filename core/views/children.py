from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from core.forms import ChildRegistrationForm
from core.models import Child

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
            messages.success(
                request,
                f"Labarik '{child.first_name}' rejistu ho susesu. Kodigu nia: {child.user_id}"
            )
            return redirect('children_list')
    else:
        form = ChildRegistrationForm()
    return render(request,'core/child_registration.html', {'form': form})

@login_required
def edit_child(request, child_id):
    child = get_object_or_404(Child, id=child_id, parent=request.user)
    if request.method == 'POST':
        form = ChildRegistrationForm(request.POST, instance=child)
        if form.is_valid():
            form.save()
            messages.success(request, f"Labarik '{child.first_name}' aktualiza ho susesu.")
            return redirect('children_list')
    else:
        form = ChildRegistrationForm(instance=child)
    return render(request, 'core/edit_child.html', {'form': form, 'child': child})

@login_required
def delete_child(request, child_id):
    child = get_object_or_404(Child, id=child_id, parent=request.user)
    if request.method == 'POST':
        name = child.first_name
        child.delete()
        messages.warning(request, f"Child '{name}' has been deleted.")
        return redirect('children_list')
    return render(request, 'core/delete_child.html', {'child': child})
