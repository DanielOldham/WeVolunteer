import json
from datetime import datetime, date

from dateutil.relativedelta import relativedelta
from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from django.http import Http404
from django.utils import timezone
from unittest.mock import patch

from core.models import Event, Organization, OrganizationAdministrator
from core.views import (
    get_events_by_month_and_year,
    about,
    events_get_next_month_events_as_sse,
    event_details,
    event_add,
    event_edit, organization_details_get_next_past_events_as_sse, organization_details, organization_edit,
)
from datastar_py.consts import ElementPatchMode

class MiscViewsTests(TestCase):
    def test_about_view_renders(self):
        response = about(RequestFactory().get("/about/"))
        self.assertEqual(response.status_code, 200)


class EventViewsTests(TestCase):
    """
    Test class for the Event related core views.
    """

    def setUp(self):
        # create user, organization, and admin links
        self.org = Organization.objects.create(name="Org")
        self.user = User.objects.create_user(username="john", password="password")
        OrganizationAdministrator.objects.create(user=self.user, organization=self.org)

        # create events for various months
        today = date.today()
        Event.objects.create(
            title="Oct Event",
            organization=self.org,
            date=today,
            start_time=datetime.now().time(),
            end_time=(datetime.now().replace(hour=16, minute=0).time()),
        )
        future_month = (today.replace(day=1) + relativedelta(days=32)).replace(day=1)
        Event.objects.create(
            title="Nov Event",
            organization=self.org,
            date=future_month,
            start_time=datetime.now().time(),
            end_time=datetime.now().time(),
        )

    def test_get_events_by_month_and_year(self):
        month_year = timezone.now().date()
        qs = get_events_by_month_and_year(month_year)
        self.assertEqual(list(qs.values_list("title", flat=True)), ["Oct Event"])

    def test_events_view_renders_and_monthly_events(self):
        client = Client()
        response = client.get("")
        self.assertEqual(response.status_code, 200)
        self.assertIn("monthly_events", response.context)
        self.assertEqual(len(response.context["monthly_events"]), 3)

    @patch("core.views.respond_via_sse")
    def test_get_next_month_events_sse_success(self, mock_respond_via_sse):
        respond_sse_msg = "respond via sse called"
        mock_respond_via_sse.return_value = respond_sse_msg

        today = timezone.now().date()
        req_dict = {"current_month": today.month, "current_year": today.year}
        request = RequestFactory().get("events/get_next_month", {"datastar": json.dumps(req_dict)})

        # respond_via_sse should be called when there are events
        response = events_get_next_month_events_as_sse(request)
        called_args, called_kwargs = mock_respond_via_sse.call_args
        next_date = today + relativedelta(months=+1)

        mock_respond_via_sse.assert_called()
        self.assertEqual(response, respond_sse_msg)
        self.assertEqual(called_kwargs['signals']['current_month'], next_date.month)
        self.assertEqual(called_kwargs['signals']['current_year'], next_date.year)
        self.assertEqual(called_kwargs['selector'], '#appended-monthly-event-list')
        self.assertEqual(called_kwargs['patch_mode'], ElementPatchMode.APPEND)


    @patch("core.views.patch_signals_respond_via_sse")
    def test_get_next_month_events_sse_calls_patch_signals_when_no_more_events(self, mock_patch_signals):
        patch_msg = "patch signals called"
        mock_patch_signals.return_value = patch_msg

        req_dict = {"current_month": 1, "current_year": 9999}
        no_event_req = RequestFactory().get("events/get_next_month", {"datastar": json.dumps(req_dict)})

        # no more events triggers patch_signals_respond_via_sse
        result = events_get_next_month_events_as_sse(no_event_req)
        self.assertEqual(result, patch_msg)
        called_args, called_kwargs = mock_patch_signals.call_args
        self.assertEqual(called_args[0]['more_events'], False)

    @patch("core.views.patch_signals_respond_via_sse")
    def test_get_next_month_events_sse_calls_patch_signals_when_no_datastar_dict(self, mock_patch_signals):
        patch_msg = "patch signals called"
        mock_patch_signals.return_value = patch_msg

        # missing datastar triggers patch_signals_respond_via_sse
        bad_req = RequestFactory().get("events/get_next_month")
        result = events_get_next_month_events_as_sse(bad_req)
        self.assertEqual(result, patch_msg)
        mock_patch_signals.assert_called()
        called_args, called_kwargs = mock_patch_signals.call_args
        self.assertEqual(called_args[0]['next_month_events_error'], True)

    def test_event_details_success(self):
        client = Client()
        event = Event.objects.first()
        response = client.get(f"/events/{event.id}")

        self.assertEqual(response.status_code, 200)
        self.assertIn("event", response.context)

    def test_event_details_not_found(self):
        request = RequestFactory().get("/events/9999")
        with self.assertRaises(Http404):
            event_details(request, 9999)

    @patch("core.views.render")
    def test_event_add_get(self, mock_render):
        request = RequestFactory().get("/events/add")
        request.user = self.user
        event_add(request)
        mock_render.assert_called()

    def test_event_add_post_valid(self):
        post_data = {
            "title": "New Event",
            "organization": self.org.id,
            "date": date.today(),
            "start_time": "10:00AM",
            "end_time": "12:00PM",
        }
        request = RequestFactory().post("/events/add", post_data)
        request.user = self.user
        with patch("core.views.EventForm") as mock_event_form:
            mock_form = mock_event_form.return_value
            mock_form.is_valid.return_value = True
            mock_form.save.return_value = Event.objects.first()
            with patch("core.views.redirect", return_value="redirect success"):
                result = event_add(request)
                self.assertEqual(result, "redirect success")

    @patch("core.views.render")
    def test_event_edit_get(self, mock_render):
        event = Event.objects.first()
        request = RequestFactory().get(f"/events/edit/{event.id}")
        request.user = self.user
        with patch("core.views.EventForm") as mock_event_form:
            event_edit(request, event_id=event.id)
            mock_event_form.assert_called_with(instance=event, user=self.user)

        self.assertTrue(mock_render.called)

    @patch("core.views.login_required", lambda x=None, **kwargs: (lambda y: y))
    @patch("core.views.permission_required", lambda *a, **kw: (lambda y: y))
    def test_event_edit_not_found(self):
        event_id = 10
        request = RequestFactory().get(f"/events/edit/{event_id}")
        request.user = self.user
        with self.assertRaises(Http404):
            event_edit(request, event_id=event_id)

    def test_event_edit_post_valid(self):
        event = Event.objects.first()
        post_data = {
            "title": "Edit Event",
            "organization": self.org.id,
            "date": timezone.now().date(),
            "start_time": "10:00AM",
            "end_time": "12:00PM",
        }
        request = RequestFactory().post(f"/events/edit/{event.id}", post_data)
        request.user = self.user
        with patch("core.views.EventForm") as mock_event_form:
            mock_form = mock_event_form.return_value
            mock_form.is_valid.return_value = True
            mock_form.save.return_value = None
            with patch("core.views.redirect", return_value="edit redirect") as mock_redirect:
                response = event_edit(request, event_id=event.id)
                self.assertTrue(mock_form.save.called)
                self.assertEqual(response, "edit redirect")

class OrganizationViewsTests(TestCase):
    """
    Test class for the Organization related core views.
    """
    def setUp(self):
        self.org = Organization.objects.create(name="Test Org")
        self.user = User.objects.create_user(username="admin", password="password")
        OrganizationAdministrator.objects.create(user=self.user, organization=self.org)

        # create 2 upcoming events and 4 past events
        today = timezone.now().date()
        Event.objects.create(title="Upcoming 1", organization=self.org, date=today, start_time="10:00", end_time="11:00")
        Event.objects.create(title="Upcoming 2", organization=self.org, date=today, start_time="12:00", end_time="13:00")
        for i in range(4):
            Event.objects.create(title=f"Past {i}", organization=self.org, date=today.replace(day=1), start_time="09:00", end_time="10:00")

    def test_organizations_view_renders_and_context(self):
        response = Client().get("/organizations/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("org_list", response.context)
        self.assertIn("org_event_counts", response.context)
        self.assertIn(self.org, response.context["org_list"])
        self.assertEqual(
            response.context["org_event_counts"][self.org.id],
            2  # only 2 upcoming events count
        )

    def test_organization_details_view_success(self):
        response = Client().get(f"/organizations/{self.org.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["org"], self.org)
        self.assertEqual(len(list(response.context["upcoming_events"])), 2)
        self.assertEqual(len(list(response.context["past_events"])), 3)  # max 3 past events shown
        self.assertEqual(response.context["past_events_count"], 3)
        self.assertEqual(len(response.context["past_events_shown"]), 3)

    def test_organization_details_view_404(self):
        request = RequestFactory().get("/organizations/9999")
        with self.assertRaises(Http404):
            organization_details(request, 9999)

    @patch("core.views.render")
    @patch("core.views.respond_via_sse")
    def test_organization_details_get_next_past_events_as_sse_success(self, mock_respond_sse, mock_render):
        mock_respond_sse.return_value = "sse_response"
        past_events_count = 2
        past_events_shown = []

        qdict = {
            "past_events_count": past_events_count,
            "past_events_shown": past_events_shown
        }
        request = RequestFactory().get(f"/organizations/{self.org.id}/next_past_events", {"datastar": json.dumps(qdict)})

        response = organization_details_get_next_past_events_as_sse(request, self.org.id)

        self.assertEqual(response, "sse_response")
        mock_render.assert_called_once()
        mock_respond_sse.assert_called_once()

        called_args, called_kwargs = mock_respond_sse.call_args
        self.assertIn("signals", called_kwargs)
        self.assertIn("past_events_shown", called_kwargs["signals"])
        self.assertIn("selector", called_kwargs)
        self.assertEqual(called_kwargs["patch_mode"], ElementPatchMode.APPEND)

    @patch("core.views.render")
    @patch("core.views.respond_via_sse")
    def test_organization_details_get_next_past_events_as_sse_sends_more_events_false(self, mock_respond_sse, mock_render):
        mock_respond_sse.return_value = "sse_response"
        past_events_count = 2
        past_events_shown = list(Event.objects.filter(organization=self.org, date__lt=timezone.now().date()).values_list("pk", flat=True))

        qdict = {
            "past_events_count": past_events_count,
            "past_events_shown": past_events_shown
        }
        request = RequestFactory().get(f"/organizations/{self.org.id}/next_past_events",
                                       {"datastar": json.dumps(qdict)})

        response = organization_details_get_next_past_events_as_sse(request, self.org.id)
        self.assertEqual(response, "sse_response")

        called_args, called_kwargs = mock_respond_sse.call_args
        # more_events signal should be set to false
        self.assertFalse(called_kwargs["signals"]["more_events"])

    @patch("core.views.patch_signals_respond_via_sse")
    def test_organization_details_get_next_past_events_as_sse_no_org(self, mock_patch_signals):
        mock_patch_signals.return_value = "patch_called"
        request = RequestFactory().get("/organizations/9999/next_past_events", {"datastar": "{}"})
        with self.assertRaises(Http404):
            organization_details_get_next_past_events_as_sse(request, 9999)

    @patch("core.views.patch_signals_respond_via_sse")
    def test_organization_details_get_next_past_events_as_sse_bad_datastar(self, mock_patch_signals):
        mock_patch_signals.return_value = "patch_called"
        request = RequestFactory().get(f"/organizations/{self.org.id}/next_past_events")
        response = organization_details_get_next_past_events_as_sse(request, self.org.id)
        self.assertEqual(response, "patch_called")
        mock_patch_signals.assert_called_once()
        args, kwargs = mock_patch_signals.call_args
        self.assertTrue(args[0].get("past_events_error"))

    @patch("core.views.render")
    def test_organization_edit_get(self, mock_render):
        request = RequestFactory().get(f"/organizations/edit/{self.org.id}")
        request.user = self.user

        with patch("core.views.OrganizationForm") as mock_form:
            organization_edit(request, org_id=self.org.id)
            mock_form.assert_called_with(instance=self.org)

        args, kwargs = mock_render.call_args
        mock_render.assert_called_once()
        self.assertIn("form", kwargs["context"])
        self.assertEqual(kwargs["context"]["action"], "Edit")

    def test_organization_edit_not_found(self):
        request = RequestFactory().get("/organizations/edit/9999")
        request.user = self.user
        with self.assertRaises(Http404):
            organization_edit(request, org_id=9999)

    def test_organization_edit_post_valid(self):
        post_data = {"name": "New Org Name", "about": "New about"}
        request = RequestFactory().post(f"/organizations/edit/{self.org.id}", post_data)
        request.user = self.user

        with patch("core.views.OrganizationForm") as mock_org_form:
            mock_form = mock_org_form.return_value
            mock_form.is_valid.return_value = True
            mock_form.save.return_value = None
            with patch("core.views.redirect", return_value="redirected") as mock_redirect:
                response = organization_edit(request, org_id=self.org.id)
                mock_org_form.assert_called_with(request.POST, instance=self.org)
                self.assertTrue(mock_form.is_valid.called)
                self.assertTrue(mock_form.save.called)
                mock_redirect.assert_called_with("core:org-details", self.org.id)
                self.assertEqual(response, "redirected")

    # def test_organization_edit_post_invalid(self):
    #     post_data = {"name": "Duplicate Name", "about": "about"}
    #     request = RequestFactory().post(f"/organizations/edit/{self.org.id}", post_data)
    #     request.user = self.user
    #
    #     with patch("core.views.OrganizationForm") as mock_org_form:
    #         mock_form = mock_org_form.return_value
    #         mock_form.is_valid.return_value = False
    #         with patch("core.views.render") as mock_render:
    #             organization_edit(request, org_id=self.org.id)
    #             mock_org_form.assert_called_with(request.POST, instance=self.org)
    #             self.assertFalse(mock_form.save.called)
    #             mock_render.assert_called_once()
    #             args, kwargs = mock_render.call_args
    #             self.assertIn("form", kwargs["context"])
    #             self.assertEqual(kwargs["context"]["action"], "Edit")
