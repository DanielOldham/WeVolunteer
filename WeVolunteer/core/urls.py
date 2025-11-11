from . import views
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

app_name = 'core'
urlpatterns = [
    path('', views.events, name='events'),
    path('about/', views.about, name='about'),
    path('events/get_next_month', views.events_get_next_month_events_as_sse, name='get-next-month-events'),
    path('events/<event_id>', views.event_details, name='event-details'),
    path('events/add/', views.event_add, name='event-add'),
    path('events/edit/<event_id>', views.event_edit, name='event-edit'),
    path('events/delete/<event_id>', views.event_delete, name='event-delete'),
    path('organizations/', views.organizations, name='organizations'),
    path('organizations/<org_id>', views.organization_details, name='org-details'),
    path('organizations/get_next_past_events/<org_id>', views.organization_details_get_next_past_events_as_sse, name='get-next-past-events'),
    path('organizations/edit/<org_id>', views.organization_edit, name='org-edit'),
    path('organization_contacts/add', views.organization_contact_add, name='org-contact-add'),
    path('organization_contacts/edit/<org_contact_id>', views.organization_contact_edit, name='org-contact-edit'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)