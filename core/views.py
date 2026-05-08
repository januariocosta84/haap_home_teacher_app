# core/views.py

from re import escape
from django.db.models import Count, Q
from django.db import connection
from django.http.response import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from io import BytesIO
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from datetime import datetime

from core.models import AdministrativePost, Aldeia, ApkVersion, AppUsageLog, Child, Municipality, Suco, User,ActivityResult
from core.services.whatsapp_service import WhatsAppService
from .forms import ApkVersionForm, ChildRegistrationForm, LoginForm, ParentRegisterForm, ParentRegistrationForm, ProfileImageForm, UserRegistrationForm
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views import View
from django.views.generic import ListView
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib import messages
from django.conf import settings
from django.contrib.auth import get_user_model
import uuid
from django.shortcuts import render


@login_required
def home(request):
    return render(request, 'core/home.html')

def parent(request):
    return render(request,'core/parent_home.html' )

#child registration
@login_required
def child_registration(request):
    if request.method == 'POST':
        form = ChildRegistrationForm(request.POST)
        if form.is_valid():
            child = form.save(commit=False)
            child.parent = request.user  # assign logged-in parent
            child.save()
            messages.success(request, f"Labarik '{child.first_name}' rejistu ho susesu.")
            return redirect('core:children_list')  # redirect to a list page (define this URL)
    else:
        form = ChildRegistrationForm()
    #return render(request, 'children/register_child.html', {'form': form})
    return render(request,'core/child_registration.html' , {'form': form})
# Edit child details
@login_required
def edit_child(request, child_id):
    child = get_object_or_404(Child, id=child_id, parent=request.user)
    if request.method == 'POST':
        form = ChildRegistrationForm(request.POST, instance=child)
        if form.is_valid():
            form.save()
            messages.success(request, f"Labarik '{child.first_name}' aktualiza ho susesu.")
            return redirect('core:children_list')
        else:
            messages.error(request, "Iha problema iha aktualizasaun labarik.")
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
        return redirect('core:children_list')
    return render(request, 'core/delete_child.html', {'child': child})
@login_required
def children_list(request):
    print("Request user:", request.user.id)
    children = Child.objects.filter(parent=request.user).order_by('-created_at')
    return render(request, 'core/children_list.html', {'children': children})

@login_required
def upload_apk(request):
    if request.method == 'POST':
        form = ApkVersionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "APK version uploaded successfully.")
            return redirect('core:apk_list')
    else:
        form = ApkVersionForm()
    return render(request, 'apk/upload_apk.html', {'form': form})

@login_required
def edit_apk(request, apk_id):
    apk = get_object_or_404(ApkVersion, id=apk_id)
    if request.method == 'POST':
        form = ApkVersionForm(request.POST, instance=apk)
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
    return render(request, 'apk/apk_list.html', {'apks': apks})

@login_required
def update_profile_image(request):
    if request.method == "POST":
        form = ProfileImageForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("core:home")  # redirect to your profile page (adjust name)
    else:
        form = ProfileImageForm(instance=request.user)
    return render(request, "users/update_profile_image.html", {"form": form})

@login_required
def profile_view(request):
    return render(request, "users/profile.html", {"user": request.user})

def admin_parent_child_list(request):
    # Dummy dataset: 10 parents × 2 children = 20 children
    parents = []
    for i in range(1, 11):
        parent = {
            "username": f"parent{i}",
            "email": f"parent{i}@example.com",
            "children": [
                {"first_name": f"Child{i}A", "year_of_birth": 2020, "age_group": "Group A: 3-4 years"},
                {"first_name": f"Child{i}B", "year_of_birth": 2018, "age_group": "Group B: 5-6 years"},
            ],
        }
        parents.append(parent)

    # Flatten parent-child pairs for pagination
    parent_child_list = []
    for parent in parents:
        for child in parent["children"]:
            parent_child_list.append({
                "parent_username": parent["username"],
                "parent_email": parent["email"],
                "child_first_name": child["first_name"],
                "year_of_birth": child["year_of_birth"],
                "age_group": child["age_group"],
            })

    # Paginate: 5 rows per page
    paginator = Paginator(parent_child_list, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "core/parent_child_list.html", {"page_obj": page_obj})

def parent_register(request):
    if request.method == 'POST':
        form = ParentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Will be activated after WhatsApp verification
            user.save()

            # TODO: Send WhatsApp message with verification link and temp password
            # Example: send_whatsapp_verification(user)

            messages.success(
                request,
                f"Thank you! A verification link has been sent to {user.whatsapp_number} via WhatsApp."
            )
            return redirect('core:parent_register')  # Redirect to success or thank you page
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ParentRegistrationForm()

    return render(request, 'core/parent_register.html', {'form': form})

# AJAX endpoint to check if WhatsApp number already exists
def check_whatsapp_number(request):
    number = request.GET.get('number', '').strip()
    #number = escape(number).replace(' ', '')  # remove spaces

    if number:
        # # Normalize number by ensuring + prefix if needed
        # if not number.startswith('+'):
        #     number = '+' + number
        exists = User.objects.filter(whatsapp_number=number).exists()
        print("Number:", number, "Exists:", exists)
        return JsonResponse({'exists': exists, 'number': number})

    return JsonResponse({'error': 'WhatsApp number not provided'}, status=400)
##Login form

def user_login(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            whatsapp_number = form.cleaned_data["username"]  # mapped to whatsapp_number
            password = form.cleaned_data["password"]

            user = authenticate(request, username=whatsapp_number, password=password)
            print(user)
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
                    return redirect("login")
            else:
                messages.error(request, "Invalid WhatsApp number or password")
    else:
        form = LoginForm()

    return render(request, "users/login_file.html", {"form": form})

def user_logout(request):
    logout(request)
    return redirect("core:login")


@login_required
# def moe_admin_dashboard(request):

#     return render(request, "dashboards/moe_admin.html")

def moe_admin_dashboard(request):
    context = {
        "all_users": User.objects.count(),
        "parents": User.objects.filter(role="parent").count(),
        "municipality_analysts": User.objects.filter(role="municipality_analyst").count(),
        "children": Child.objects.count(),
    }
    return render(request, "dashboards/moe_admin.html", context=context)

@login_required
def municipality_dashboard(request):
    """Dashboard for Municipality Analyst"""
    municipality = request.user.municipality

   # COUNT
    children_count = Child.objects.filter(
        parent__municipality=municipality
    ).count()

    parents_count = User.objects.filter(
        role="parent",
        municipality=municipality
    ).count()

    # LIST
    children_list = Child.objects.filter(
        parent__municipality=municipality
    )

    parents_list = User.objects.filter(
            role="parent",
            municipality=municipality
    )

    teachers_count = User.objects.filter(
        role="teacher",
        municipality=municipality
    ).count()
    teachers_list = User.objects.filter(role="teacher", municipality=municipality)
    teachers_count = teachers_list.count()

    context = {
        "municipality": municipality,
        "children_count": children_count,
        "parents_count": parents_count,
        "teachers_count": teachers_count,
        "children_list": children_list,
        "parents_list": parents_list,
        "teachers_list": teachers_list,
        "teachers_count": teachers_count,
    }
    return render(request, "dashboards/municipality_dashboard.html", context)

@login_required
def teacher_dashboard(request):
    """Dashboard for Teacher"""
    # Count all children linked to this teacher’s municipality
    # COUNT
    municipality = request.user.municipality
    children_count = Child.objects.filter(
        parent__municipality=municipality
    ).count()

    parents_count = User.objects.filter(
        role="parent",
        municipality=municipality
    ).count()

    # LIST
    children_list = Child.objects.filter(
        parent__municipality=municipality
    )

    parents_list = User.objects.filter(
            role="parent",
            municipality=municipality
    )
    children_count = Child.objects.filter(
        parent__municipality=request.user.municipality
    ).count()

    # Teacher can also see how many parents are in their municipality
    parents_count = User.objects.filter(
        role="parent",
        municipality=request.user.municipality
    ).count()

    context = {
        "municipality": municipality,
        "parents_count": parents_count,
        "parents_list": parents_list,
        "children_count": children_count,
        "children_list": children_list,
    }
    return render(request, "dashboards/teacher_dashboard.html", context)

def parent_dashboard(request):
    return render(request, "dashboard/parent.html")

# def municipality_dashboard(request):
#     return render(request, "dashboard/municipality.html")

# def teacher_dashboard(request):
#     return render(request, "dashboard/teacher.html")



class UserManagementView(View):
    def get(self, request):
        # Only MoE admins can access user management
        if not request.user.is_authenticated or request.user.role != "moe_admin":
            messages.error(request, "Aksesu negadu.")
            return redirect("core:home")
        
        # Query users by role
        parents = User.objects.filter(role="parent")
        teachers = User.objects.filter(role="teacher")
        analysts = User.objects.filter(role="municipality_analyst")
        admins = User.objects.filter(role="moe_admin")

        context = {
            "parents": parents,
            "teachers": teachers,
            "analysts": analysts,
            "admins": admins,
        }
        return render(request, "users/user_management.html", context)
    

def parent_list(request):
    parents = User.objects.filter(role="parent").order_by('-date_joined')
    
    # Filter by municipality if provided
    municipality_id = request.GET.get("municipality")
    if municipality_id:
        parents = parents.filter(municipality_id=municipality_id)
    
    paginator = Paginator(parents, 10)  # 10 parents per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    # Get all municipalities for dropdown
    municipalities = Municipality.objects.all().order_by("name")
    
    return render(request, "parents/parent_list.html", {
        "page_obj": page_obj,
        "municipalities": municipalities
    })

def is_valid_uuid(value):
    try:
        uuid.UUID(str(value))
        return True
    except ValueError:
        return False

# class AppUsageLogListView(ListView):
#     model = ActivityResult
#     template_name = "dashboards/logs.html"
#     context_object_name = "logs"
#     paginate_by = 10

#     def get_queryset(self):
#         user = self.request.user

#         queryset = ActivityResult.objects.select_related(
#             "parent",
#             "student",
#             "student__parent"
#         ).order_by("-created_at")

#         # ------------------------
#         # 1. Text search filter
#         # ------------------------
#         activity = self.request.GET.get("activity")
#         if activity:
#             queryset = queryset.filter(activity_name__icontains=activity)

#         # ------------------------
#         # 2. Role-based filters
#         # ------------------------
#         if user.role == "parent":
#             queryset = queryset.filter(parent=user)

#         elif user.role == "municipality_analyst":
#             if user.municipality:
#                 queryset = queryset.filter(
#                     Q(parent__municipality=user.municipality) |
#                     Q(student__parent__municipality=user.municipality)
#                 )
#             else:
#                 return ActivityResult.objects.none()

#         elif user.role == "teacher":
#             queryset = queryset.filter(
#                 student__parent__municipality=user.municipality
#             )

#         elif user.role == "moe_admin":
#             pass  # no restrictions

#         else:
#             return ActivityResult.objects.none()

#         # ------------------------
#         # 3. Parent filter (dropdown or querystring)
#         # ------------------------
#         parent_id = self.request.GET.get("parent")

#         if parent_id and is_valid_uuid(parent_id):
#             queryset = queryset.filter(parent__id=parent_id)

#         # ------------------------
#         # 4. Student filter (children of the selected parent)
#         # ------------------------
#         student_id = self.request.GET.get("student")

#         if student_id and is_valid_uuid(student_id):
#             queryset = queryset.filter(student__id=student_id)

#         return queryset
class AppUsageLogListView(ListView):
    model = ActivityResult
    template_name = "dashboards/logs.html"
    context_object_name = "logs"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # build GET params without "page"
        query = self.request.GET.copy()
        if "page" in query:
            query.pop("page")

        ctx["querystring"] = query.urlencode()

        return ctx
    def get_queryset(self):
        user = self.request.user

        queryset = ActivityResult.objects.select_related(
            "parent",
            "student",
            "student__parent"
        ).order_by("-created_at")

        # 1. Text search
        activity = self.request.GET.get("activity")
        if activity:
            queryset = queryset.filter(activity_name__icontains=activity)

        # 2. Role-based filter
        if user.role == "parent":
            queryset = queryset.filter(parent=user)

        elif user.role == "municipality_analyst":
            if user.municipality:
                queryset = queryset.filter(
                    Q(parent__municipality=user.municipality) |
                    Q(student__parent__municipality=user.municipality)
                )
            else:
                return ActivityResult.objects.none()

        elif user.role == "teacher":
            queryset = queryset.filter(
                student__parent__municipality=user.municipality
            )

        elif user.role == "moe_admin":
            pass  # list ALL

        else:
            return ActivityResult.objects.none()

        # 3. Parent filter
        parent_id = self.request.GET.get("parent")
        if parent_id and is_valid_uuid(parent_id):
            queryset = queryset.filter(parent__id=parent_id)

        # 4. Student filter
        student_id = self.request.GET.get("student")
        if student_id and is_valid_uuid(student_id):
            queryset = queryset.filter(student__id=student_id)

        return queryset

    # ----------------------------------------------------------
    # NEW SECTION — ensure moe_admin sees ALL parents & students
    # ----------------------------------------------------------
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        parent_id = self.request.GET.get("parent")
        student_id = self.request.GET.get("student")

        # SELECT PARENTS BASED ON ROLE
        if user.role == "moe_admin":
            ctx["filter_parents"] = User.objects.all()
        elif user.role in ["teacher", "municipality_analyst"]:
            ctx["filter_parents"] = User.objects.filter(
                municipality=user.municipality
            )
        else:
            ctx["filter_parents"] = User.objects.filter(id=user.id)

        # SELECT STUDENTS (depends on parent filter)
        if parent_id and is_valid_uuid(parent_id):
            ctx["filter_students"] = Child.objects.filter(parent_id=parent_id)
        else:
            if user.role == "moe_admin":
                ctx["filter_students"] = Child.objects.all()
            else:
                ctx["filter_students"] = Child.objects.filter(
                    parent__municipality=user.municipality
                )

        # Keep selected filters
        ctx["selected_activity"] = self.request.GET.get("activity", "")
        ctx["selected_parent"] = parent_id
        ctx["selected_student"] = student_id

        return ctx


class ChildrenReportView(ListView):
    model = Child
    template_name = "dashboards/children_report.html"
    context_object_name = "children"

    def get_queryset(self):
        queryset = Child.objects.select_related(
            "parent__municipality",
            "parent__administrative_post",
            "parent__suco",
            "parent__aldeia"
        )

        municipality_id = self.request.GET.get("municipality")
        ap_id = self.request.GET.get("administrative_post")
        suco_id = self.request.GET.get("suco")
        aldeia_id = self.request.GET.get("aldeia")

        if municipality_id:
            queryset = queryset.filter(parent__municipality_id=municipality_id)
        if ap_id:
            queryset = queryset.filter(parent__administrative_post_id=ap_id)
        if suco_id:
            queryset = queryset.filter(parent__suco_id=suco_id)
        if aldeia_id:
            queryset = queryset.filter(parent__aldeia_id=aldeia_id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        municipality_id = self.request.GET.get("municipality")
        ap_id = self.request.GET.get("administrative_post")
        suco_id = self.request.GET.get("suco")
        aldeia_id = self.request.GET.get("aldeia")

        # Always show all municipalities
        context["municipalities"] = Municipality.objects.all().order_by("name")

        # Filter dropdowns dynamically
        if municipality_id:
            context["administrative_posts"] = AdministrativePost.objects.filter(
                municipality_id=municipality_id
            ).order_by("name")
        else:
            context["administrative_posts"] = AdministrativePost.objects.none()

        if ap_id:
            context["sucos"] = Suco.objects.filter(
                administrative_post_id=ap_id
            ).order_by("name")
        else:
            context["sucos"] = Suco.objects.none()

        if suco_id:
            context["aldeias"] = Aldeia.objects.filter(
                suco_id=suco_id
            ).order_by("name")
        else:
            context["aldeias"] = Aldeia.objects.none()

        # 📊 Filtered reports (use the same filters as queryset)
        base_qs = self.get_queryset()

        context["report_by_municipality"] = (
            base_qs.values("parent__municipality__name")
            .annotate(total=Count("id"))
            .order_by("parent__municipality__name")
        )

        context["report_by_ap"] = (
            base_qs.values(
                "parent__administrative_post__name",
                "parent__municipality__name"
            )
            .annotate(total=Count("id"))
            .order_by("parent__municipality__name", "parent__administrative_post__name")
        )

        context["report_by_suco"] = (
            base_qs.values(
                "parent__suco__name",
                "parent__administrative_post__name"
            )
            .annotate(total=Count("id"))
            .order_by("parent__administrative_post__name", "parent__suco__name")
        )

        context["report_by_aldeia"] = (
            base_qs.values(
                "parent__aldeia__name",
                "parent__suco__name"
            )
            .annotate(total=Count("id"))
            .order_by("parent__suco__name", "parent__aldeia__name")
        )

        return context

class LoadAdministrativePosts(View):
    def get(self, request):
        municipality_id = request.GET.get("municipality_id")
        posts = AdministrativePost.objects.filter(municipality_id=municipality_id).values("id", "name")
        return JsonResponse(list(posts), safe=False)

class LoadSucos(View):
    def get(self, request):
        post_id = request.GET.get("administrative_post_id")
        sucos = Suco.objects.filter(administrative_post_id=post_id).values("id", "name")
        return JsonResponse(list(sucos), safe=False)

class LoadAldeias(View):
    def get(self, request):
        suco_id = request.GET.get("suco_id")
        aldeias = Aldeia.objects.filter(suco_id=suco_id).values("id", "name")
        return JsonResponse(list(aldeias), safe=False)
    
class ParentRegisterView(View):
    def get(self, request):
        form = ParentRegisterForm()
        return render(request, "registration/parent_register.html", {"form": form})

    def post(self, request):
        form = ParentRegisterForm(request.POST)
        if form.is_valid():
            print(form.cleaned_data)
            form.save()
            return redirect("core:login")  # redirect after success
        return render(request, "registration/parent_register.html", {"form": form})

User = get_user_model()

@login_required

# MoE Admin can register new users (teachers, analysts, other admins)
def register_user(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # # Generate password reset link
            # uid = urlsafe_base64_encode(force_bytes(user.pk))
            # token = default_token_generator.make_token(user)
            # reset_url = request.build_absolute_uri(
            #     reverse("password_reset_confirm", kwargs={"uidb64": uid, "token": token})
            # )

            # # Send reset email
            # subject = "Set your HAAP account password"
            # message = f"Hello {user.first_name},\n\nYour account has been created. Please set your password by clicking the link below:\n{reset_url}\n\nThank you!"
            # send_mail(subject, message, "admin@haap.com", [user.email])

            messages.success(request, f"User {user.first_name} created successfully and password setup email sent.")
            return redirect("core:moe_admin_dashboard")
    else:
        form = UserRegistrationForm()

    return render(request, "users/register_user.html", {"form": form})


@login_required
def view_user(request, user_id):
    """Simple view for a single user (MoE admin only)."""
    if request.user.role != "moe_admin":
        messages.error(request, "Aksesu negadu.")
        return redirect("core:user_management")

    user = get_object_or_404(User, id=user_id)
    return render(request, "users/view_user.html", {"obj": user})


@login_required
def edit_user(request, user_id):
    """Edit an existing user (MoE admin only)."""
    if request.user.role != "moe_admin":
        messages.error(request, "Aksesu negadu.")
        return redirect("core:user_management")

    user_obj = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        form = UserRegistrationForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "User updated successfully.")
            return redirect("core:user_management")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserRegistrationForm(instance=user_obj)

    return render(request, "users/edit_user.html", {"form": form, "user_obj": user_obj})


@login_required
def delete_user(request, user_id):
    """Delete a user (MoE admin only). Shows confirmation form on GET, deletes on POST."""
    if request.user.role != "moe_admin":
        messages.error(request, "Aksesu negadu.")
        return redirect("core:user_management")

    user_obj = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        name = f"{user_obj.first_name} {user_obj.last_name}"
        user_obj.delete()
        messages.warning(request, f"User '{name}' has been deleted.")
        return redirect("core:user_management")

    return render(request, "users/confirm_delete_user.html", {"user_obj": user_obj})

class LatestApkView(ListView):
    model = ApkVersion
    template_name = "apk/latest_version.html"
    context_object_name = "versions"

    def get_queryset(self):
        # Show only latest version(s) - usually one, but in case of multiple
        return ApkVersion.objects.filter(is_latest=True).order_by("-released_at")


@login_required
def export_parents_pdf(request):
    """Export filtered parents list to PDF"""
    municipality_id = request.GET.get("municipality")
    
    # Get parents based on municipality filter
    parents = User.objects.filter(role="parent").order_by('-date_joined')
    
    if municipality_id:
        parents = parents.filter(municipality_id=municipality_id)
        municipality = Municipality.objects.get(id=municipality_id)
        municipality_name = municipality.name
    else:
        municipality_name = "All Municipalities"
    
    # Create PDF in memory
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
    story = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=12,
        alignment=1  # center
    )
    
    # Title
    title = Paragraph(f"Lista Parentes - {municipality_name}", title_style)
    story.append(title)
    story.append(Spacer(1, 0.2*inch))
    
    # Metadata
    metadata_style = ParagraphStyle(
        'Metadata',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
    )
    metadata = Paragraph(f"<i>Gerada iha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</i>", metadata_style)
    story.append(metadata)
    story.append(Spacer(1, 0.3*inch))
    
    # Total count
    total_parents = parents.count()

    # Prepare table data
    table_data = [['Naran', 'WhatsApp', 'Email', 'Munisipiu']]
    
    for parent in parents:
        table_data.append([
            f"{parent.first_name} {parent.last_name}",
            parent.whatsapp_number or "-",
            parent.email or "-",
            str(parent.municipality) if parent.municipality else "-"
        ])
    
    # Add total summary above table
    summary_style = ParagraphStyle(
        'Summary',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=8,
    )
    story.append(Paragraph(f"Total Parentes: <b>{total_parents}</b>", summary_style))

    if len(table_data) == 1:  # Only header
        story.append(Paragraph("Walha dados no filtru ne'e.", styles['Normal']))
    else:
        # Create table
        table = Table(table_data, colWidths=[2*inch, 1.5*inch, 2*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        story.append(table)
    
    # Build PDF
    doc.build(story)
    pdf_buffer.seek(0)
    
    # Return PDF as response
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    filename = f"parents_list_{municipality_name.replace(' ', '_')}_{datetime.now().strftime('%d%m%Y')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response



def custom_404(request, exception):
    return render(request, '404.html', status=404)

