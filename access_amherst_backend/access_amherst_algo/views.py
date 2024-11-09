from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.management import call_command
import json
import pytz
from .parse_database import (
    filter_events,
    get_unique_locations,
    get_events_by_hour,
    get_category_data,
)
from .generate_map import create_map, add_event_markers, generate_heatmap
from .models import Event

from datetime import timedelta

# View to run db_saver command
def run_db_saver(request):
    call_command("db_saver")
    return redirect("../")


# View to run events_list_creator command
def run_events_list_creator(request):
    call_command("events_list_creator")
    return redirect("../")


# View to run json_saver command
def run_json_saver(request):
    call_command("json_saver")
    return redirect("../")


# View to run rss_fetcher command
def run_rss_fetcher(request):
    call_command("rss_fetcher")
    return redirect("../")


# View to run the hub_data_cleaner command
def run_hub_data_cleaner(request):
    call_command("hub_data_cleaner")
    return redirect("../")


def home(request):
    """Render home page with search and filter functionality."""
    events = filter_events(
        query=request.GET.get("query", ""),
        locations=request.GET.getlist("locations"),
        start_date=request.GET.get("start_date"),
        end_date=request.GET.get("end_date"),
    )
    return render(
        request,
        "access_amherst_algo/home.html",
        {
            "events": events,
            "query": request.GET.get("query", ""),
            "selected_locations": request.GET.getlist("locations"),
            "start_date": request.GET.get("start_date"),
            "end_date": request.GET.get("end_date"),
            "unique_locations": get_unique_locations(),
        },
    )


def map_view(request):
    """Render map view with event markers."""
    events = Event.objects.exclude(
        latitude__isnull=True, longitude__isnull=True
    )
    folium_map = create_map([42.37031303771378, -72.51605520950432])
    add_event_markers(folium_map, events)
    return render(
        request,
        "access_amherst_algo/map.html",
        {"map_html": folium_map._repr_html_()},
    )


def data_dashboard(request):
    """Render dashboard with event insights and heatmap."""
    est = pytz.timezone("America/New_York")

    events = Event.objects.all()

    context = {
        "events_by_hour": get_events_by_hour(events, est),
        "category_data": get_category_data(
            events.exclude(categories__isnull=True), est
        ),
        "map_html": generate_heatmap(
            events, est
        )._repr_html_(),  # Convert to HTML here
    }

    return render(request, "access_amherst_algo/dashboard.html", context)


@csrf_exempt
def update_heatmap(request):
    """Update heatmap based on selected time range from request."""
    if request.method == "POST":
        data = json.loads(request.body)
        est = pytz.timezone("America/New_York")

        folium_map = generate_heatmap(
            events=Event.objects.all(),
            timezone=est,
            min_hour=data.get("min_hour", 7),
            max_hour=data.get("max_hour", 22),
        )

        map_html = folium_map._repr_html_()  # Convert to HTML here
        return JsonResponse({"map_html": map_html})


def calendar_view(request):
    """Render calendar view with events in weekly format."""
    # Define the time range and initialize days
    times = [f"{hour}:00" for hour in range(8, 22)]  # 8 AM to 10 PM
    days_of_week = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    # Organize events by day and hour
    events_by_day = {day: {time: [] for time in times} for day in days_of_week}
    events = Event.objects.all()

    # Categorize events by day of the week and their start time hour
    for event in events:
        event_day = event.start_time.strftime('%A')  # Get day name (e.g., 'Monday')
        event_time = event.start_time.strftime('%H:00')  # Get hour in "HH:00" format

        if event_day in events_by_day and event_time in events_by_day[event_day]:
            events_by_day[event_day][event_time].append(event)

    context = {
        'times': times,
        'days_of_week': days_of_week,
        'events_by_day': events_by_day,
    }
    return render(request, 'access_amherst_algo/calendar.html', context)