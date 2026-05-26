from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from core.models import Child, User
from .models import Classroom, ClassroomChild
from django.views.generic import ListView
from .forms import AddChildToClassForm, ChildCodeEnrollmentForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from preschools.models import PreschoolTeacher
from preschools.models import Preschool
from .models import Classroom


@method_decorator(login_required, name='dispatch')
class TeacherSchoolListView(View):
    """Teacher's dashboard showing all schools they teach at"""
    template_name = "klase/teacher_school_list.html"

    def get(self, request):
        # Get all schools where the teacher is assigned
        preschool_teachers = PreschoolTeacher.objects.filter(
            teacher=request.user,
            is_active=True
        ).select_related('preschool')

        preschools_data = []
        total_students = 0

        for pt in preschool_teachers:
            preschool = pt.preschool
            # Get classrooms in this school taught by this teacher
            classrooms = Classroom.objects.filter(
                preschool=preschool,
                teacher=request.user
            ).prefetch_related('enrollments')
            
            classroom_count = classrooms.count()
            student_count = sum(c.enrollments.count() for c in classrooms)
            total_students += student_count

            preschools_data.append({
                'id': preschool.id,
                'name': preschool.name,
                'preschool_type': preschool.get_preschool_type_display(),
                'classroom_count': classroom_count,
                'student_count': student_count,
                'is_primary': pt.is_primary,
            })

        context = {
            'preschools': preschools_data,
            'schools': preschools_data,  # For sidebar
            'total_schools': len(preschools_data),
            'total_students': total_students,
        }

        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class SchoolClassroomListView(View):
    """Show all classrooms in a specific school"""
    template_name = "klase/school_classroom_list.html"

    def get(self, request, preschool_id):
        # Verify teacher has access to this preschool
        preschool = get_object_or_404(
            Preschool,
            id=preschool_id
        )

        preschool_teacher = get_object_or_404(
            PreschoolTeacher,
            preschool=preschool,
            teacher=request.user,
            is_active=True
        )

        # Get classrooms in this school taught by this teacher
        classrooms = Classroom.objects.filter(
            preschool=preschool,
            teacher=request.user
        ).prefetch_related('enrollments', 'enrollments__child')

        classroom_data = []
        total_students = 0
        group_a_count = 0
        group_b_count = 0

        for classroom in classrooms:
            enrollments = classroom.enrollments.all()
            student_count = enrollments.count()
            total_students += student_count

            # Count by age group
            for enrollment in enrollments:
                if enrollment.child.age_group == 'A':
                    group_a_count += 1
                elif enrollment.child.age_group == 'B':
                    group_b_count += 1

            classroom_data.append({
                'id': classroom.id,
                'name': classroom.name,
                'group': classroom.group,
                'student_count': student_count,
                'students': list(enrollments.values('child__first_name', 'child__user_id', 'child__age_group')),
            })

        context = {
            'preschool': {
                'id': preschool.id,
                'name': preschool.name,
                'preschool_type': preschool.get_preschool_type_display(),
            },
            'classrooms': classroom_data,
            'total_classrooms': len(classroom_data),
            'total_students': total_students,
            'group_a_count': group_a_count,
            'group_b_count': group_b_count,
            # For sidebar
            'schools': [],
            'total_schools': 1,
        }

        # Get all schools for sidebar
        all_preschools = PreschoolTeacher.objects.filter(
            teacher=request.user,
            is_active=True
        ).select_related('preschool')

        schools_for_sidebar = []
        for pt in all_preschools:
            ps = pt.preschool
            classrooms_count = Classroom.objects.filter(
                preschool=ps,
                teacher=request.user
            ).count()
            schools_for_sidebar.append({
                'id': ps.id,
                'name': ps.name,
                'classroom_count': classrooms_count,
            })

        context['schools'] = schools_for_sidebar
        context['total_schools'] = len(schools_for_sidebar)

        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class ClassroomDetailView(View):
    """Show classroom details with enrolled students and option to add children"""
    template_name = "klase/classroom_detail.html"

    def get(self, request, classroom_id):
        classroom = get_object_or_404(
            Classroom,
            id=classroom_id,
            teacher=request.user
        )

        enrollments = classroom.enrollments.all().select_related('child')
        form = ChildCodeEnrollmentForm()

        # Get all schools for sidebar
        all_preschools = PreschoolTeacher.objects.filter(
            teacher=request.user,
            is_active=True
        ).select_related('preschool')

        schools_for_sidebar = []
        total_students_all = 0
        for pt in all_preschools:
            ps = pt.preschool
            classrooms_list = Classroom.objects.filter(
                preschool=ps,
                teacher=request.user
            ).prefetch_related('enrollments')
            classrooms_count = classrooms_list.count()
            students_count = sum(c.enrollments.count() for c in classrooms_list)
            total_students_all += students_count
            schools_for_sidebar.append({
                'id': ps.id,
                'name': ps.name,
                'classroom_count': classrooms_count,
            })

        context = {
            'classroom': {
                'id': classroom.id,
                'name': classroom.name,
                'group': classroom.group,
                'preschool_id': classroom.preschool.id,
                'preschool_name': classroom.preschool.name,
            },
            'students': list(enrollments.values('child__id', 'child__first_name', 'child__user_id', 'child__age_group')),
            'student_count': enrollments.count(),
            'form': form,
            # For sidebar
            'schools': schools_for_sidebar,
            'total_schools': len(schools_for_sidebar),
            'total_students': total_students_all,
        }

        return render(request, self.template_name, context)

    def post(self, request, classroom_id):
        classroom = get_object_or_404(
            Classroom,
            id=classroom_id,
            teacher=request.user
        )

        form = ChildCodeEnrollmentForm(request.POST)

        if form.is_valid():
            child_code = form.cleaned_data['child_code']

            # Find child by user_id (the code)
            child = Child.objects.filter(user_id=child_code).first()

            if not child:
                messages.error(request, f"Child with code '{child_code}' not found.")
                return redirect('klase:classroom-detail', classroom_id=classroom.id)

            # Check if child's age group matches classroom group
            if child.age_group != classroom.group:
                messages.error(
                    request,
                    f"Child age group '{child.age_group}' does not match classroom group '{classroom.group}'."
                )
                return redirect('klase:classroom-detail', classroom_id=classroom.id)

            # Check if already enrolled in this classroom
            if ClassroomChild.objects.filter(classroom=classroom, child=child, is_active=True).exists():
                messages.warning(request, f"{child.first_name} is already enrolled in this class.")
                return redirect('klase:classroom-detail', classroom_id=classroom.id)

            # Create enrollment
            ClassroomChild.objects.create(
                classroom=classroom,
                child=child,
                is_active=True
            )

            messages.success(request, f"{child.first_name} has been added to {classroom.name}.")
            return redirect('klase:classroom-detail', classroom_id=classroom.id)
        else:
            messages.error(request, "Invalid child code.")
            return redirect('klase:classroom-detail', classroom_id=classroom.id)


class TeacherDashboardView(View):

    template_name = "klase/teacher_dashboard.html"

    def get(self, request):

        # Get all classrooms for this teacher
        classrooms = Classroom.objects.filter(
            teacher=request.user
        ).prefetch_related("enrollments", "enrollments__child")

        classroom_data = []

        total_students = 0

        for c in classrooms:

            student_count = c.enrollments.count()
            total_students += student_count

            classroom_data.append({
                "id": c.id,
                "class_name": c.class_name,
                "group": c.group,
                "student_count": student_count
            })

        context = {
            "classrooms": classroom_data,
            "total_classes": classrooms.count(),
            "total_students": total_students
        }

        return render(request, self.template_name, context)
class TeacherProDashboardView(View):

    template_name = "klase/teacher_dashboard_pro.html"

    def get(self, request):

        classrooms = Classroom.objects.filter(
            teacher=request.user
        ).prefetch_related("enrollments")

        data = []

        total_students = 0
        group_a = 0
        group_b = 0

        for c in classrooms:

            count = c.enrollments.count()
            total_students += count

            group_a += c.enrollments.filter(child__age_group='A').count()
            group_b += c.enrollments.filter(child__age_group='B').count()

            data.append({
                "id": c.id,
                "name": c.class_name,
                "group": c.group,
                "students": count
            })

        return render(request, self.template_name, {
            "classrooms": data,
            "total_classes": classrooms.count(),
            "total_students": total_students,
            "group_a": group_a,
            "group_b": group_b,
        })
    
class AjaxRegisterChild(View):
    def post(self, request):

        classroom_id = request.POST.get("classroom_id")
        parent_code = request.POST.get("user_id")
        first_name = request.POST.get("first_name")

        classroom = Classroom.objects.get(id=classroom_id)

        parent = User.objects.filter(username=parent_code).first()

        if not parent:
            return JsonResponse({"error": "Parent not found"}, status=400)

        child = Child.objects.create(
            parent=parent,
            first_name=first_name,
            year_of_birth=2019,
            age_group=classroom.group
        )

        ClassroomChild.objects.create(
            classroom=classroom,
            child=child,
            added_by=request.user
        )

        return JsonResponse({"success": True})

class ClassroomListView(ListView):
    model = Classroom
    template_name = "klase/classroom_list.html"
    context_object_name = "classrooms"

    def get_queryset(self):
        return Classroom.objects.all()
    
class AddChildToClassroomView(View):
    template_name = "klase/classroom_detail.html"

    def post(self, request, classroom_id):

        classroom = get_object_or_404(
            Classroom,
            id=classroom_id,
            teacher=request.user
        )

        form = AddChildToClassForm(request.POST)

        if not form.is_valid():
            messages.error(request, "Invalid data.")
            return redirect("classroom-detail", classroom_id=classroom.id)

        user_id = form.cleaned_data["user_id"]
        first_name = form.cleaned_data["first_name"]

        # 1. Find child
        child = Child.objects.filter(
            user_id=user_id,
            first_name__iexact=first_name
        ).first()

        if not child:
            messages.error(request, "Child not found.")
            return redirect("classroom-detail", classroom_id=classroom.id)

        # 2. Check if already assigned
        if hasattr(child, "classroom_enrollment"):
            messages.error(
                request,
                f"{child.first_name} already belongs to a class."
            )
            return redirect("classroom-detail", classroom_id=classroom.id)

        # 3. Age group validation
        if child.age_group != classroom.group:
            messages.error(
                request,
                "Child age group does not match classroom."
            )
            return redirect("classroom-detail", classroom_id=classroom.id)

        # 4. Create enrollment
        ClassroomChild.objects.create(
            classroom=classroom,
            child=child,
            added_by=request.user
        )

        messages.success(request, "Child added successfully.")

        return redirect("classroom-detail", classroom_id=classroom.id)

class EnrollChildView(LoginRequiredMixin, View):
    def post(self, request, classroom_id):
        classroom = get_object_or_404(Classroom, id=classroom_id)
        form = ChildCodeEnrollmentForm(request.POST)

        if form.is_valid():
            code = form.cleaned_data['child_code']
            child = get_object_or_404(Child, child_code=code)

            # deactivate previous active classroom
            ClassroomChild.objects.filter(
                child=child,
                is_active=True
            ).update(is_active=False)

            # assign to new classroom
            ClassroomChild.objects.get_or_create(
                classroom=classroom,
                child=child,
                defaults={'is_active': True}
            )

            messages.success(request, 'Child enrolled successfully.')

        return redirect('classroom_detail', classroom_id=classroom.id)