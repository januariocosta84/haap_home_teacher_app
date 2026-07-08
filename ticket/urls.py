from django.urls import path

from .views import (
    SupportTicketAddItemsView,
    SupportTicketCreateView,
    SupportTicketDetailView,
    SupportTicketListView,
    SupportTicketUpdateView,
    get_ticket_by_number,
    notification_list,
    notification_mark_all_read,
    notification_mark_read,
    notification_unread_count,
)

app_name = 'ticket'

urlpatterns = [

    # ── Support Tickets CRUD ──────────────────────────────────
    path('',                        SupportTicketListView.as_view(),   name='ticket_list'),
    path('create/',                 SupportTicketCreateView.as_view(), name='ticket_create'),
    path('<uuid:pk>/',              SupportTicketDetailView.as_view(), name='ticket_detail'),
    path('<uuid:pk>/update/',       SupportTicketUpdateView.as_view(), name='ticket_update'),
    path('<uuid:pk>/items/',        SupportTicketAddItemsView.as_view(), name='ticket_items_add'),

    # ── Notifications ─────────────────────────────────────────
    path('notifications/',                             notification_list,          name='notification_list'),
    path('notifications/count/',                       notification_unread_count,  name='notification_count'),
    path('notifications/<uuid:notification_id>/read/', notification_mark_read,     name='notification_mark_read'),
    path('notifications/read-all/',                    notification_mark_all_read, name='notification_mark_all_read'),

    # ── AJAX ──────────────────────────────────────────────────
    path('ajax/by-number/', get_ticket_by_number, name='ajax_ticket_by_number'),
]
