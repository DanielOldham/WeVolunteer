from django.shortcuts import render

from core.models import Event


def events(request):
    """
    Render the events page
    """
    event_list = Event.objects.all()
    context = {
        'events': event_list,
    }

    return render(request, 'events.html', context)