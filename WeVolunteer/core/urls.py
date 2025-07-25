from . import views
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

app_name = 'core'
urlpatterns = [
    path('', views.events, name='events'),
    path('events/get_more_events', views.get_monthly_events_as_sse, name='get-monthly-events'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)