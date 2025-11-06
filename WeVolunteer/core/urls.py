from . import views
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

app_name = 'core'
urlpatterns = [
    path('', views.events, name='events'),
    path('about/', views.about, name='about'),
    path('events/get_next_month', views.get_next_month_events_as_sse, name='get-next-month-events'),
    path('events/<event_id>', views.event_details, name='event-details'),
    path('events/add/', views.event_add, name='event-add'),
    path('events/edit/<event_id>', views.event_edit, name='event-edit'),
    path('organizations/', views.organizations, name='organizations'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)