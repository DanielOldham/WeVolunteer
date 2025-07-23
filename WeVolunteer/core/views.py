from datetime import datetime

from dateutil.relativedelta import relativedelta
from django.shortcuts import render

from core.models import Event


def get_events_by_month_and_year(month_year: datetime):
    return Event.objects.filter(date__month=month_year.month, date__year=month_year.year).order_by('date')


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
        month = current_month + i
        year = current_year
        if month > 12:
            month = 1
            year += 1

        events_date = datetime(year=year, month=month, day=1)
        queryset = get_events_by_month_and_year(events_date)
        if i == 0:
            queryset = queryset.filter(date__gte=now)

        monthly_events[f"{events_date.strftime('%B')} {events_date.year}"] = queryset

    context = {
        'monthly_events': monthly_events,
    }

    return render(request, 'events.html', context)