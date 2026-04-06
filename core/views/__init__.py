from .auth import user_login, user_logout
from .children import children_list, child_registration, edit_child, delete_child
from .dashboards import moe_admin_dashboard, municipality_dashboard, teacher_dashboard
from .activity_logs import  AppUsageLogListView
from .exports import export_parents_pdf
from .ajax import check_whatsapp_number
from .apk import download_apk, upload_apk, edit_apk, apk_list, LatestApkView
from .profile import profile_view, update_profile_image, change_password
from .parents import parents_list, add_parent, edit_parent, delete_parent, ParentRegisterView, parent_register
from .main import home, parent_home, admin_parent_child_list
from .reports import ChildrenReportView
from .ajax_loads import get_children_by_parent, get_parents_by_municipality, load_administrative_posts, load_sucos, load_aldeias
from .user_management import UserManagementView, register_user, view_user, edit_user, delete_user

__all__ = [
    'user_login', 'user_logout',
    'children_list', 'child_registration', 'edit_child', 'delete_child',
    'moe_admin_dashboard', 'municipality_dashboard', 'teacher_dashboard',
    'AppUsageLogListView', 'export_parents_pdf', 'check_whatsapp_number',
    'download_apk', 'upload_apk', 'edit_apk', 'apk_list', 'LatestApkView',
    'profile_view', 'update_profile_image', 'change_password',
    'parents_list', 'add_parent', 'edit_parent', 'delete_parent', 'ParentRegisterView', 'parent_register',
    'home', 'parent_home', 'admin_parent_child_list',
    'ChildrenReportView', 'UserManagementView', 'register_user', 'view_user', 'edit_user', 'delete_user',
    'get_children_by_parent', 'get_parents_by_municipality', 'load_administrative_posts', 'load_sucos', 'load_aldeias',
  
]
