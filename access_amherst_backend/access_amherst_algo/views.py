from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_date
from datetime import date, datetime, timedelta
import json
from .parse_database import (
    filter_events,
    get_unique_locations,
    get_events_by_hour,
    get_category_data,
)
from .generate_map import create_map, add_event_markers, generate_heatmap
from .parse_database import filter_events_by_category, get_unique_categories
from .models import Event


def make_naive(event):
    """Ensure start_time and end_time are naive datetimes."""
    if event.start_time and event.start_time.tzinfo:
        event.start_time = event.start_time.replace(tzinfo=None)
    if event.end_time and event.end_time.tzinfo:
        event.end_time = event.end_time.replace(tzinfo=None)


def home(request):
    query = request.GET.get("query", "")
    locations = request.GET.getlist("locations")
    categories = request.GET.getlist("categories")

    today = date.today()
    default_start_date = today
    default_end_date = today + timedelta(days=7)

    start_date = parse_date(request.GET.get("start_date")) if request.GET.get("start_date") else default_start_date
    end_date = parse_date(request.GET.get("end_date")) if request.GET.get("end_date") else default_end_date

    # Get events and apply consistent naive datetime parsing
    events = filter_events(
        query=query,
        locations=locations, 
        start_date=start_date,
        end_date=end_date,
    )
    events = filter_events_by_category(events, categories).order_by("start_time")
    for event in events:
        make_naive(event)

    return render(
        request,
        "access_amherst_algo/home.html",
        {
            "events": events,
            "query": query,
            "selected_locations": locations,
            "selected_categories": categories,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "unique_locations": get_unique_locations(),
            "unique_categories": get_unique_categories(),
        },
    )


def map_view(request):
    events = Event.objects.exclude(latitude__isnull=True, longitude__isnull=True)
    # Apply naive datetime conversion right after query
    time_standardized_events = []
    for event in events:
        time_standardized_events.append(make_naive(event))
    events = time_standardized_events
        
    folium_map = create_map([42.37031303771378, -72.51605520950432])
    add_event_markers(folium_map, events)
    return render(request, "access_amherst_algo/map.html", {"map_html": folium_map._repr_html_()})


def data_dashboard(request):
    events = Event.objects.all()
    # Apply naive datetime conversion right after initial query
    for event in events:
        make_naive(event)

    events_with_categories = events.exclude(categories__isnull=True)
    
    context = {
        "events_by_hour": get_events_by_hour(events),
        "category_data": get_category_data(events_with_categories),
        "map_html": generate_heatmap(events)._repr_html_(),
    }
    return render(request, "access_amherst_algo/dashboard.html", context)


@csrf_exempt
def update_heatmap(request):
    if request.method == "POST":
        data = json.loads(request.body)
        events = Event.objects.all()
        # Apply naive datetime conversion right after query
        for event in events:
            make_naive(event)

        folium_map = generate_heatmap(
            events=events,
            min_hour=data.get("min_hour", 7),
            max_hour=data.get("max_hour", 22),
        )
        return JsonResponse({"map_html": folium_map._repr_html_()})


def calendar_view(request):
    """Render calendar view with events."""
    today = date.today()
    days_of_week = [(today + timedelta(days=i)) for i in range(7)]
    times = [datetime.strptime(f"{hour}:00", "%H:%M").time() for hour in range(5, 23)]

    start_date = days_of_week[0]
    end_date = days_of_week[-1]
    events = filter_events(start_date=start_date, end_date=end_date)

    events_by_day = {}
    for day in days_of_week:
        events_by_day[day.strftime('%Y-%m-%d')] = []

    for event in events:
        make_naive(event)

        event_date = event.start_time.date()
        event_date_str = event_date.strftime('%Y-%m-%d')
        if event_date_str in events_by_day:
            event_obj = {
                "title": event.title,
                "location": event.location,
                "start_time": event.start_time,
                "end_time": event.end_time,
                "top": (event.start_time.hour - 7) * 60 + event.start_time.minute,
                "height": ((event.end_time.hour - event.start_time.hour) * 60 +
                          (event.end_time.minute - event.start_time.minute)),
                "column": 0,
                "columns": 1
            }
            events_by_day[event_date_str].append(event_obj)

    for day, events in events_by_day.items():
        if not events:
            continue

        events.sort(key=lambda x: x['start_time'])

        for i, event in enumerate(events):
            overlapping = []
            for other in events:
                if event != other and is_overlapping(event, other):
                    overlapping.append(other)

            if overlapping:
                max_columns = len(overlapping) + 1
                taken_columns = set()
                for e in overlapping:
                    if 'column' in e:
                        taken_columns.add(e['column'])

                for col in range(max_columns):
                    if col not in taken_columns:
                        event['column'] = col
                        break

                event['columns'] = max_columns
                for e in overlapping:
                    e['columns'] = max_columns

    return render(
        request,
        "access_amherst_algo/calendar.html",
        {
            "days_of_week": days_of_week,
            "times": times,
            "events_by_day": events_by_day,
        },
    )


def is_overlapping(event1, event2):
    """Check if two events overlap in time."""
    return not (event1['end_time'] <= event2['start_time'] or 
               event2['end_time'] <= event1['start_time'])