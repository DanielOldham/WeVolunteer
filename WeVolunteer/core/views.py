import json
from datetime import datetime

from datastar_py.consts import ElementPatchMode
from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, redirect
from django.utils import timezone
from rules.contrib.views import permission_required, objectgetter

from WeVolunteer.utils import respond_via_sse, patch_signals_respond_via_sse
from core.forms import EventForm
from core.models import Event, EventDescriptors, EventLocationDescriptors, Organization


def get_events_by_month_and_year(month_year: datetime.date):
    """
    Get a queryset of events by the given month and year.

    :param month_year: datetime.date containing the desired month and year, day is ignored
    """

    return Event.objects.filter(date__month=month_year.month, date__year=month_year.year).order_by('date', 'start_time', 'title')


def about(request):
    """
    Django view.
    Render the about page.
    """
    return render(request, "about.html")


def events(request):
    """
    Django view.
    Render the events page.
    """

    monthly_events = {}
    now = timezone.now().date()
    events_date = now

    num_months = 3
    for i in range(num_months):
        events_date = now + relativedelta(months=+i)
        queryset = get_events_by_month_and_year(events_date)
        if i == 0:
            queryset = queryset.filter(date__gte=now)

        monthly_events[f"{events_date.strftime('%B')} {events_date.year}"] = queryset

    context = {
        'monthly_events': monthly_events,
        'current_month': events_date.month,
        'current_year': events_date.year,
    }

    return render(request, 'events.html', context)



def events_get_next_month_events_as_sse(request):
    """
    Datastar SSE Django View. Called from the Events page.

    Locate the currently displayed month and year from the request datastar dictionary,
    calculate the subsequent month and year, generate the corresponding events html,
    and return as an SSE.
    Also send the incremented month/year back to the frontend as patch signals.
    """

    today = timezone.now()
    signals = {"next_month_events_error": False}

    # get current month and year from datastar signals dict
    try:
        qdict = json.loads(request.GET.get("datastar"))
        month = qdict.get("current_month", today.month)
        year = qdict.get("current_year", today.year)
    except TypeError:
        signals["next_month_events_error"] = True
        return patch_signals_respond_via_sse(signals)

    # increment month by using relative delta in case the year rolls over
    events_date = datetime(year=year, month=month, day=1)
    events_date = events_date + relativedelta(months=+1)

    # check and see if any future events
    if not Event.objects.filter(date__gte=events_date).exists():
        signals["more_events"] = False
        return patch_signals_respond_via_sse(signals)

    queryset = get_events_by_month_and_year(events_date)

    monthly_events = {f"{events_date.strftime('%B')} {events_date.year}": queryset}
    signals["current_month"] = events_date.month
    signals["current_year"] = events_date.year
    context = {
        'monthly_events': monthly_events,
    }

    html_response = render(
        request,
        "partials/monthly_event_list.html#monthly-event-list",
        context
    )
    return respond_via_sse(html_response, signals=signals, selector='#appended-monthly-event-list', patch_mode=ElementPatchMode.APPEND)


def event_details(request, event_id):
    """
    Django view.
    Display a detailed page for one specific event.
    """

    event = Event.objects.filter(id=event_id).first()
    if event:
        return render(request, "event_details.html", {"event": event})
    else:
        raise Http404("Event does not exist")


@login_required()
@permission_required("events.add_event", raise_exception=True)
def event_add(request):
    """
    Django view.
    Display and handle submission of the form for a new Event.
    """

    if request.method == "POST":
        form = EventForm(request.POST, user=request.user)
        if form.is_valid():
            event = form.save()
            return redirect('core:event-details', event.id)
    else:
        form = EventForm(user=request.user)

    context = {
        'form': form,
        'action': 'Add',
        'event_descriptors': EventDescriptors,
        'location_descriptors': EventLocationDescriptors,
    }
    return render(request, "event_form.html", context)


@login_required()
@permission_required("events.change_event", fn=objectgetter(Event, "event_id"), raise_exception=True)
def event_edit(request, event_id: int):
    """
    Django view.
    Display and handle submission of the form for an existing Event.
    """

    # don't need to check if event exists because the permission required middleware checks automatically
    event = Event.objects.filter(id=event_id).first()

    if request.method == "POST":
        form = EventForm(request.POST, instance=event, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('core:event-details', event.id)
    else:
        form = EventForm(instance=event, user=request.user)

    context = {
        'form': form,
        'action': 'Edit',
        'event_descriptors': EventDescriptors,
        'location_descriptors': EventLocationDescriptors,
    }
    return render(request, "event_form.html", context)


def organizations(request):
    """
    Django view.
    Render the organizations page.
    """
    upcoming_events = Event.objects.filter(date__gte=timezone.now().date())
    orgs = Organization.objects.all()
    org_event_counts = {org.id: len(upcoming_events.filter(organization=org)) for org in orgs}

    context = {
        "org_list": orgs,
        "org_event_counts": org_event_counts,
    }
    return render(request, "organizations.html", context=context)


def organization_details(request, org_id: int):
    """
    Django view.
    Display a detailed page for one organization.
    """
    org = Organization.objects.filter(id=org_id).first()
    if not org:
        raise Http404("Organization does not exist")

    now = timezone.now().date()
    org_events = Event.objects.filter(organization=org)
    upcoming_events = org_events.filter(date__gte=now)

    # display and load 3 past events at a time
    past_events_count = 3
    all_past_events = org_events.filter(date__lt=now).order_by('-date', 'start_time', 'title')
    past_events = all_past_events[:past_events_count] if len(all_past_events) > past_events_count else all_past_events
    past_events_shown = [event.id for event in past_events]

    context = {
        "org": org,
        "upcoming_events": upcoming_events,
        "past_events": past_events,
        "past_events_count": past_events_count,
        "past_events_shown": past_events_shown,
    }
    return render(request, "organization_details.html", context)


def organization_details_get_next_past_events_as_sse(request, org_id):
    """
    Datastar SSE Django View. Called from an Organization Details page.

    Locate the currently displayed past events and the count to load from the request datastar dictionary,
    calculate the slice of additional past events to show, generate the html response, and return as an SSE.
    Also send the new list of displayed past event ids back as a patched signal.
    """

    org = Organization.objects.filter(id=org_id).first()
    if not org:
        raise Http404("Organization does not exist")

    signals = {"past_events_error": False}
    try:
        qdict = json.loads(request.GET.get("datastar"))
        past_events_count = qdict.get("past_events_count", 0)
        past_events_shown = qdict.get("past_events_shown", 0)
    except TypeError:
        signals["past_events_error"] = True
        return patch_signals_respond_via_sse(signals)

    now = timezone.now().date()
    all_past_events = Event.objects.filter(organization=org, date__lt=now).order_by('-date', 'start_time', 'title')

    # exclude events which are already shown
    past_events = all_past_events.exclude(id__in=past_events_shown)
    if len(past_events) > past_events_count:
        past_events = past_events[:past_events_count]
    else:
        signals["more_events"] = False

    signals["past_events_shown"] = past_events_shown + [event.id for event in past_events]
    context = { "event_list": past_events, }
    html_response = render(request, "partials/event_list.html#event-list", context)
    return respond_via_sse(
        html_response,
        signals=signals,
        selector='#appended-past-events',
        patch_mode=ElementPatchMode.APPEND
    )
