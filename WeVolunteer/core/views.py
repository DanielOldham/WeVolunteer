import json
from datetime import datetime, timedelta
from time import sleep

from datastar_py.consts import FragmentMergeMode
from dateutil.relativedelta import relativedelta
from django.shortcuts import render

from WeVolunteer.utils import respond_via_sse
from core.models import Event


def get_events_by_month_and_year(month_year: datetime):
    return Event.objects.filter(date__month=month_year.month, date__year=month_year.year).order_by('date', 'start_time')


def events(request):
    """
    Render the events page
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


def get_monthly_events_as_sse(request):
    today = datetime.today()
    month = 0
    year = 0

    try:
        qdict = json.loads(request.GET.get("datastar", "{}"))
        month = qdict.get("current_month", today.month)
        year = qdict.get("current_year", today.year)
    except TypeError:
        pass

    events_date = datetime(year=year, month=month, day=1)
    events_date = events_date + relativedelta(months=+1)
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
    return respond_via_sse(html_response, signals=signals, selector='#appended-monthly-event-list', merge_mode=FragmentMergeMode.APPEND)