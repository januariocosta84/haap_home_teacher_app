from django.urls import path

from .views import (
    SupportTicketCreateView,
    SupportTicketAddItemsView,
    SupportTicketDetailView,
    SupportTicketListView,
    SupportTicketUpdateView,
    get_ticket_by_number,
    notification_unread_count,
    notification_list,
    notification_mark_read,
    notification_mark_all_read,
)

urlpatterns = [

    path(
        'create/',
        SupportTicketCreateView.as_view(),
        name='support-ticket-create'
    ),

    path(
        '<uuid:pk>/items/',
        SupportTicketAddItemsView.as_view(),
        name='support-ticket-add-items'
    ),

    path(
        '<uuid:pk>/',
        SupportTicketDetailView.as_view(),
        name='support-ticket-detail'
    ),

    path(
        '<uuid:pk>/update/',
        SupportTicketUpdateView.as_view(),
        name='support-ticket-update'
    ),

    path(
        'list/',
        SupportTicketListView.as_view(),
        name='support-ticket-list'
    ),

    path(
        'ajax/get-by-number/',
        get_ticket_by_number,
        name='ajax-get-ticket'
    ),

    # Notification endpoints
    path(
        'notifications/count/',
        notification_unread_count,
        name='notification-count'
    ),
    path(
        'notifications/',
        notification_list,
        name='notification-list'
    ),
    path(
        'notifications/<uuid:notification_id>/read/',
        notification_mark_read,
        name='notification-mark-read'
    ),
    path(
        'notifications/read-all/',
        notification_mark_all_read,
        name='notification-read-all'
    ),
]
