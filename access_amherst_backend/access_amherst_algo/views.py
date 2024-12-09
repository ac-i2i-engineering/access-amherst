from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.management import call_command
from django.utils import timezone
from dateutil import parser
from datetime import date, datetime, timedelta
import json
import pytz
from .parse_database import (
    filter_events,
    get_unique_locations,
    get_events_by_hour,
    get_category_data,
)
from .generate_map import create_map, add_event_markers, generate_heatmap
from .parse_database import filter_events_by_category, get_unique_categories
from .models import Event


CATEGORY_EMOJI_MAP = {
    'Social': '👥',  # Two people
    'Group Business': '💼',  # Briefcase
    'Athletics': '🏃',  # Person Running
    'Meeting': '📅',  # Calendar
    'Community Service': '🌍',  # Globe
    'Arts': '🎭🎨',  # Performing Arts and Artist Palette
    'Concert': '🎵',  # Musical Notes
    'Arts and Craft': '🧶',  # Yarn
    'Workshop': '🛠️',  # Hammer and Wrench
    'Cultural': '🌏',  # Globe
    'Thoughtful Learning': '🧠',  # Brain
    'Spirituality': '☸️',  # Wheel of Dharma
}


def home(request):
    """Render home page with search, location, date, and category filters."""
    # Get query parameters
    query = request.GET.get("query", "")
    locations = request.GET.getlist("locations")
    categories = request.GET.getlist("categories")

    # Set local time to EST
    est = pytz.timezone("America/New_York")
    timezone.activate(est)

    # Calculate default start and end dates (1-week range)
    today = timezone.now().astimezone(est).date()
    default_start_date = today
    default_end_date = today + timedelta(days=7)

    # Use user-provided dates or defaults
    start_date = (
        parser.parse(request.GET.get("start_date")).date()
        if request.GET.get("start_date")
        else default_start_date
    )
    end_date = (
        parser.parse(request.GET.get("end_date")).date()
        if request.GET.get("end_date")
        else default_end_date
    )

    # Convert dates to UTC for database query
    start_time = datetime(
        start_date.year, start_date.month, start_date.day, 0, 0, 0, tzinfo=est
    ).astimezone(pytz.UTC)
    end_time = datetime(
        end_date.year, end_date.month, end_date.day, 23, 59, 59, tzinfo=est
    ).astimezone(pytz.UTC)

    # Filter events
    events = filter_events(
        query=query,
        locations=locations,
        start_date=start_time.date(),
        end_date=end_time.date(),
    )

    events = filter_events_by_category(events, categories)
    
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
    
@csrf_exempt
def update_gantt(request):
    """Fetch events within a specified date and time range for the Gantt chart."""
    if request.method == 'POST':
        data = json.loads(request.body)
        date_str = data.get('date')
        start_time_str = data.get('start_time')
        end_time_str = data.get('end_time')

        # Parse the date and times
        selected_date = parser.parse(date_str).date()
        start_time = parser.parse(start_time_str).time()
        end_time = parser.parse(end_time_str).time()

        # Combine date and time to create datetime objects
        start_datetime = datetime.combine(selected_date, start_time, tzinfo=pytz.timezone('America/New_York'))
        end_datetime = datetime.combine(selected_date, end_time, tzinfo=pytz.timezone('America/New_York'))

        # Convert the datetime objects to UTC for database query
        start_datetime = start_datetime.astimezone(pytz.UTC)
        end_datetime = end_datetime.astimezone(pytz.UTC)

        # Filter events within the specified date and time range
        events = Event.objects.filter(
            start_time__gte=start_datetime,
            end_time__lte=end_datetime
        )

        # Prepare event data for the response
        event_data = [{
            'name': event.title,
            'start_time': event.start_time.astimezone(pytz.timezone('America/New_York')).isoformat(),
            'end_time': event.end_time.astimezone(pytz.timezone('America/New_York')).isoformat(),
        } for event in events]

        return JsonResponse({'events': event_data})
    return JsonResponse({'error': 'Invalid request method'}, status=400)


def calendar_view(request):
    est = pytz.timezone("America/New_York")
    timezone.activate(est)
    today = timezone.now().astimezone(est).date()
    days_of_week = [(today + timedelta(days=i)) for i in range(3)]
    
    # Generate times from 5:00 AM to 11:00 PM
    times = [datetime.strptime(f"{hour}:00", "%H:%M").time() for hour in range(5, 23)]

    start_date = datetime(days_of_week[0].year, days_of_week[0].month, days_of_week[0].day, 0, 0, 0, 
                          tzinfo=pytz.timezone("America/New_York")).astimezone(pytz.UTC).date()
    end_date = datetime(days_of_week[-1].year, days_of_week[-1].month, days_of_week[-1].day, 23, 59, 59,
                        tzinfo=pytz.timezone("America/New_York")).astimezone(pytz.UTC).date()
    events = filter_events(start_date=start_date, end_date=end_date)

    events_by_day = {}
    for day in days_of_week:
        events_by_day[day.strftime('%Y-%m-%d')] = []
    
    # Update the event positioning calculation
    for event in events:
        start_time_est = event.start_time.astimezone(pytz.timezone("America/New_York"))
        end_time_est = event.end_time.astimezone(pytz.timezone("America/New_York"))

        event_date = start_time_est.date()
        event_date_str = event_date.strftime('%Y-%m-%d')
        if event_date_str in events_by_day:
            # Calculate position and height
            top = (start_time_est.hour - 5) * 45 + (start_time_est.minute / 60) * 45
            height = ((end_time_est.hour - start_time_est.hour) * 45 + 
                     ((end_time_est.minute - start_time_est.minute) / 60) * 45)
            
            event_obj = {
                "title": event.title,
                "location": event.location,
                "start_time": start_time_est,
                "end_time": end_time_est,
                "top": top,
                "height": max(height, 30),  # Minimum height for visibility
                "column": 0,
                "columns": 1
            }
            events_by_day[event_date_str].append(event_obj)

    # Calculate overlaps for each day
    for day, day_events in events_by_day.items():
        if day_events:  # Only process if there are events
            # Sort events by start time
            day_events.sort(key=lambda x: x['start_time'])
            
            # Find overlapping groups and assign columns
            current_group = []
            max_columns = 1
            
            for event in day_events:
                # Remove events from current group that don't overlap with current event
                current_group = [e for e in current_group if is_overlapping(e, event)]
                
                # Add current event to group
                current_group.append(event)
                
                # Update columns for current group
                column = 0
                used_columns = set()
                
                for e in current_group:
                    if column in used_columns:
                        column += 1
                    e['column'] = column
                    used_columns.add(column)
                
                # Update max columns for the group
                max_columns = max(max_columns, len(current_group))
            
            # Set number of columns for all events in the day
            for event in day_events:
                event['columns'] = max_columns

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
    return not (event1['end_time'] <= event2['start_time'] or 
               event2['end_time'] <= event1['start_time'])

def about(request):
    return render(request, "access_amherst_algo/about.html")