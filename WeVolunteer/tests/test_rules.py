import rules
from django.test import TestCase
from django.contrib.auth.models import User
from core.models import Organization, OrganizationAdministrator, Event
from core.rules import (
    is_event_organization_admin,
    is_organization_admin,
)


class RulesPredicateTests(TestCase):
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

    def test_is_event_organization_admin_true(self):
        """
        User is org admin and event belongs to same org.
        """
        result = is_event_organization_admin(self.user, self.event_same_org)
        self.assertTrue(result)

    def test_is_event_organization_admin_false_different_org(self):
        """
        User is org admin but event belongs to another org.
        """
        result = is_event_organization_admin(self.user, self.event_other_org)
        self.assertFalse(result)

    def test_is_event_organization_admin_false_no_admin(self):
        """
        User has no organization administrator link.
        """
        new_user = User.objects.create(username="no_admin_user")
        result = is_event_organization_admin(new_user, self.event_same_org)
        self.assertFalse(result)

    def test_is_organization_admin_true(self):
        """
        User has linked OrganizationAdministrator record.
        """
        self.assertTrue(is_organization_admin(self.user))

    def test_is_organization_admin_false(self):
        """
        User is not an organization administrator.
        """
        another_user = User.objects.create(username="guest")
        self.assertFalse(is_organization_admin(another_user))

    def test_rules_permissions_are_registered(self):
        """
        Verify that permissions were registered correctly with rules.
        """
        perms = rules.permissions.permissions
        self.assertIn("events.change_event", perms)
        self.assertIn("events.add_event", perms)

        change_rule = perms["events.change_event"]
        add_rule = perms["events.add_event"]

        self.assertIs(change_rule, is_event_organization_admin)
        self.assertIs(add_rule, is_organization_admin)

    def test_perm_behaviors(self):
        """
        Test that rules.test_rule behaves as expected.
        """

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
