from django.contrib import admin

from core.models import Organization, Event

admin.site.register(Organization)
admin.site.register(Event)