from django.urls import path

from .views import (
    SupportTicketCreateView,
    SupportTicketAddItemsView,
    SupportTicketDetailView,
    SupportTicketListView,
    SupportTicketUpdateView,
    get_ticket_by_number,
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
]
