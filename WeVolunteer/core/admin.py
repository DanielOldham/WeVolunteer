from django.contrib import admin

from core.models import Organization, OrganizationContact, Event

admin.site.register(Organization)
admin.site.register(OrganizationContact)
admin.site.register(Event)