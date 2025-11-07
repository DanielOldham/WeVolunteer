import rules
from django.contrib.auth.models import User
from core.models import Event, OrganizationAdministrator, Organization


@rules.predicate
def is_organization_admin_for_event(user: User, event: Event):
    """
    Django Rules Predicate.
    Check if the given user is an organization administrator and if the given event belongs to the org.
    """
    org_user = OrganizationAdministrator.objects.filter(user=user, organization=event.organization)
    if org_user.exists():
        return event.organization == org_user.first().organization
    else:
        return False
rules.add_perm('events.change_event', is_organization_admin_for_event)


@rules.predicate
def is_organization_admin(user: User):
    """
    Django Rules Predicate.
    Check if the given user is an organization administrator.
    """

    return OrganizationAdministrator.objects.filter(user=user).exists()
rules.add_perm('events.add_event', is_organization_admin)

@rules.predicate
def is_organization_admin_for_organization(user: User, organization: Organization):
    """
    Django Rules Predicate.
    Check if the given user is an organization administrator for the given organization.
    """

    return OrganizationAdministrator.objects.filter(user=user, organization=organization).exists()
rules.add_perm('organizations.change_organization', is_organization_admin_for_organization)