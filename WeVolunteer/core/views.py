from datetime import datetime

from dateutil.relativedelta import relativedelta
from django.shortcuts import render

from core.models import Event


def get_events_by_month_and_year(month_year: datetime):
    return Event.objects.filter(date__month=month_year.month, date__year=month_year.year).order_by('date', 'start_time')


def events(request):
    """
    Render the events page
    """
    monthly_events = {}
    now = datetime.now().date()
    current_year = now.year
    current_month = now.month

    num_months = 3
    for i in range(num_months):
        current_month += 1 ####################
        if current_month > 12:
            current_month = 1
            current_year += 1

        events_date = datetime(year=current_year, month=current_month, day=1)
        queryset = get_events_by_month_and_year(events_date)
        if i == 0:
            queryset = queryset.filter(date__gte=now)

        monthly_events[f"{events_date.strftime('%B')} {events_date.year}"] = queryset

    context = {
        'monthly_events': monthly_events,

    }

    return render(request, 'events.html', context)