import json
from datetime import datetime

from datastar_py.consts import ElementPatchMode
from dateutil.relativedelta import relativedelta
from django.shortcuts import render

from WeVolunteer.utils import respond_via_sse, patch_signals_respond_via_sse
from core.forms import EventForm
from core.models import Event, EventDescriptors


def get_events_by_month_and_year(month_year: datetime.date):
    """
    Get a queryset of events by the given month and year.

    :param month_year: datetime.date containing the desired month and year, day is ignored
    """

    return Event.objects.filter(date__month=month_year.month, date__year=month_year.year).order_by('date', 'start_time')


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
    now = datetime.today()
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


def get_next_month_events_as_sse(request):
    """
    Locate the currently displayed month and year from the request datastar dictionary,
    calculate the subsequent month and year, generate the corresponding events html,
    and return as an SSE.
    Also send the incremented month/year back to the frontend as patch signals.
    """

    today = datetime.today()
    month = 0
    year = 0

    # get current month and year from datastar signals dict
    try:
        qdict = json.loads(request.GET.get("datastar", "{}"))
        month = qdict.get("current_month", today.month)
        year = qdict.get("current_year", today.year)
    except TypeError:
        pass

    # increment month by using relativedelta in case the year rolls over
    events_date = datetime(year=year, month=month, day=1)
    events_date = events_date + relativedelta(months=+1)

    # check and see if any future events
    if not Event.objects.filter(date__gte=events_date).exists():
        signals = {
            "more_events": False,
        }

        return patch_signals_respond_via_sse(signals)

    queryset = get_events_by_month_and_year(events_date)

    monthly_events = {f"{events_date.strftime('%B')} {events_date.year}": queryset}
    signals = {
        "current_month": events_date.month,
        "current_year": events_date.year,
    }
    context = {
        'monthly_events': monthly_events,
    }

    html_response = render(
        request,
        "partials/monthly_event_list.html#monthly-event-list",
        context
    )
    return respond_via_sse(html_response, signals=signals, selector='#appended-monthly-event-list', patch_mode=ElementPatchMode.APPEND)


def event_add_or_edit(request, event_id: int=None):
    """
    Display the form for an Event.
    """

    if request.method == "GET":
        if event_id:
            event = Event.objects.get(id=event_id)
            form = EventForm(instance=event)
        else:
            form = EventForm()
    elif request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            form.save()

    context = {
        'form': form,
        'event_descriptors': EventDescriptors,
    }
    return render(request, "event_form.html", context)
