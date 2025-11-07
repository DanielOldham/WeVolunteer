import rules
from django.test import TestCase
from django.contrib.auth.models import User
from core.models import Organization, OrganizationAdministrator, Event
from core.rules import (
    is_organization_admin_for_event,
    is_organization_admin,
    is_organization_admin_for_organization,
)


class RulesPredicateTests(TestCase):
    """
    Test class for the Django Rules and Predicates.
    """

    def setUp(self):
        # Create a user and an organization
        self.user = User.objects.create(username="john_doe")
        self.org = Organization.objects.create(name="Helping Hands")
        self.other_org = Organization.objects.create(name="Other Org")

        # Create a matching admin link
        self.admin_link = OrganizationAdministrator.objects.create(
            user=self.user,
            organization=self.org,
        )

        # Create events for both orgs
        self.event_same_org = Event.objects.create(
            title="Toy Drive",
            organization=self.org,
            date="2025-12-25",
            start_time="10:00",
            end_time="12:00",
        )
        self.event_other_org = Event.objects.create(
            title="Food Prep",
            organization=self.other_org,
            date="2025-12-26",
            start_time="09:00",
            end_time="10:00",
        )

    def test_is_organization_admin_for_event_true(self):
        # user is org admin and event belongs to same org
        result = is_organization_admin_for_event(self.user, self.event_same_org)
        self.assertTrue(result)

    def test_is_organization_admin_for_event_false_different_org(self):
        # user is org admin but event belongs to another org
        result = is_organization_admin_for_event(self.user, self.event_other_org)
        self.assertFalse(result)

    def test_is_organization_admin_for_event_false_no_admin(self):
        # user has no organization administrator link
        new_user = User.objects.create(username="no_admin_user")
        result = is_organization_admin_for_event(new_user, self.event_same_org)
        self.assertFalse(result)

    def test_is_organization_admin_true(self):
        # user has linked OrganizationAdministrator record
        self.assertTrue(is_organization_admin(self.user))

    def test_is_organization_admin_false(self):
        # user is not an organization administrator
        another_user = User.objects.create(username="guest")
        self.assertFalse(is_organization_admin(another_user))

    def test_rules_permissions_are_registered(self):
        # verify that permissions were registered correctly with rules
        perms = rules.permissions.permissions
        self.assertIn("events.change_event", perms)
        self.assertIn("events.add_event", perms)

        change_rule = perms["events.change_event"]
        add_rule = perms["events.add_event"]

        self.assertIs(change_rule, is_organization_admin_for_event)
        self.assertIs(add_rule, is_organization_admin)

    def test_event_perm_behaviors(self):
        # User belongs to correct org for this event
        can_change = rules.has_perm("events.change_event", self.user, self.event_same_org)
        self.assertTrue(can_change)

        # Wrong org event
        can_change_other = rules.has_perm("events.change_event", self.user, self.event_other_org)
        self.assertFalse(can_change_other)

        # Right user for add_event
        can_add = rules.has_perm("events.add_event", self.user)
        self.assertTrue(can_add)

        # Non-admin user cannot add
        guest = User.objects.create(username="guest_add")
        self.assertFalse(rules.has_perm("events.add_event", guest))

    def test_is_organization_admin_for_organization_true(self):
        self.assertTrue(is_organization_admin_for_organization(self.user, self.org))

    def test_is_organization_admin_for_organization_false(self):
        self.assertFalse(is_organization_admin_for_organization(self.user, self.other_org))

    def test_organization_change_permission_is_registered(self):
        perms = rules.permissions.permissions
        self.assertIn("organizations.change_organization", perms)
        self.assertIs(perms["organizations.change_organization"], is_organization_admin_for_organization)

    def test_organization_perm_behaviors(self):
        # true for actual admin
        self.assertTrue(rules.has_perm("organizations.change_organization", self.user, self.org))
        # false for wrong org
        self.assertFalse(rules.has_perm("organizations.change_organization", self.user, self.other_org))
        # false for outsider
        outsider = User.objects.create(username="not_admin")
        self.assertFalse(rules.has_perm("organizations.change_organization", outsider, self.org))
