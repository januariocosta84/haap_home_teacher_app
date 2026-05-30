from django.urls import path
from .views import (
    AddChildToClassroomView, AjaxRegisterChild, ClassroomListView, 
    TeacherDashboardView, TeacherProDashboardView,
    TeacherSchoolListView, SchoolClassroomListView, ClassroomDetailView,
    RemoveStudentFromClassroomView, DownloadClassroomChildrenView
)
app_name = 'klase'
urlpatterns = [
    # Teacher main dashboard - list of schools
    path('teacher/schools/', TeacherSchoolListView.as_view(), name='teacher-schools'),
    
    # School classrooms list
    path('teacher/school/<uuid:preschool_id>/classrooms/', SchoolClassroomListView.as_view(), name='school-classrooms'),
    
    # Classroom details and add children
    path('classroom/<uuid:classroom_id>/', ClassroomDetailView.as_view(), name='classroom-detail'),
    path('classroom/<uuid:classroom_id>/add-child/', AddChildToClassroomView.as_view(), name='add-child-classroom'),
    path('classroom/<uuid:classroom_id>/remove-student/<uuid:enrollment_id>/', RemoveStudentFromClassroomView.as_view(), name='remove-student'),
    path('classroom/<uuid:classroom_id>/children/download/', DownloadClassroomChildrenView.as_view(), name='download-classroom-children'),
    
    # Legacy endpoints
    path('teacher/dashboard/', TeacherDashboardView.as_view(), name='teacher-dashboard'),
    path('teacher/dashboard/pro/', TeacherProDashboardView.as_view(), name='teacher-dashboard-pro'),
    path('ajax/register-child/', AjaxRegisterChild.as_view(), name='ajax-register-child'),
    path('classrooms/', ClassroomListView.as_view(), name='classroom-list'),
]
