from django.shortcuts import render, redirect
from django.http import JsonResponse
import json
from .models import Event
from django.core.management import call_command
from django.db.models import Count
from django.db.models.functions import ExtractHour
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
import folium
from folium.plugins import HeatMap
import pytz
from datetime import time
import urllib.parse
import re

# View to run db_saver command


def run_db_saver(request):
    call_command('db_saver')
    return redirect('../')

# View to run events_list_creator command


def run_events_list_creator(request):
    call_command('events_list_creator')
    return redirect('../')

# View to run json_saver command


def run_json_saver(request):
    call_command('json_saver')
    return redirect('../')

# View to run rss_fetcher command


def run_rss_fetcher(request):
    call_command('rss_fetcher')
    return redirect('../')


def run_hub_data_cleaner(request):
    call_command('hub_data_cleaner')
    return redirect('../')

# Home view with search functionality


def home(request):
    # Get query, location filter, start and end date from request
    query = request.GET.get('query', '')
    locations = request.GET.getlist('locations')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Filter events
    events = Event.objects.all()
    if query:
        events = events.filter(title__icontains=query)
    if locations:
        events = events.filter(map_location__in=locations)
    if start_date and end_date:
        events = events.filter(start_time__date__range=[start_date, end_date])

    # Remove duplicate events
    events = events.distinct()

    # Get unique map locations for filtering
    unique_locations = Event.objects.values_list(
        'map_location', flat=True).distinct()

    # Pass context to template
    return render(request, 'access_amherst_algo/home.html', {
        'events': events,
        'query': query,
        'selected_locations': locations,
        'start_date': start_date,
        'end_date': end_date,
        'unique_locations': unique_locations
    })


def map_view(request):
    # Fetch events with valid latitude and longitude
    events = Event.objects.exclude(
        latitude__isnull=True).exclude(
        longitude__isnull=True)

    # Initialize map centered around Amherst College
    amherst_college_coords = [42.37031303771378, -72.51605520950432]
    folium_map = folium.Map(location=amherst_college_coords, zoom_start=18)

    # Add markers for each event using latitude and longitude fields
    for event in events:
        # Format the start and end time
        start_time = event.start_time.strftime('%Y-%m-%d %H:%M')
        end_time = event.end_time.strftime('%Y-%m-%d %H:%M')

        # Google Calendar link
        google_calendar_link = (
            "https://www.google.com/calendar/render?action=TEMPLATE"
            f"&text={urllib.parse.quote(event.title)}"
            f"&dates={event.start_time.strftime('%Y%m%dT%H%M%SZ')}/{event.end_time.strftime('%Y%m%dT%H%M%SZ')}"
            f"&details={urllib.parse.quote(event.event_description)}"
            f"&location={urllib.parse.quote(event.location)}"
        )

        # Define the popup HTML
        popup_html = (
            f"<strong>{event.title}</strong><br>"
            f"{event.location} ({event.map_location})<br>"
            f"Start: {start_time}<br>"
            f"End: {end_time}<br>"
            f"<a href='{google_calendar_link}' target='_blank'>Add to Google Calendar</a>"
        )

        # Add marker with popup
        folium.Marker(
            location=[float(event.latitude), float(event.longitude)],
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(folium_map)

    # Render map as HTML
    map_html = folium_map._repr_html_()
    return render(request,
                  'access_amherst_algo/map.html',
                  {'map_html': map_html})


# Dashboard view for data insights
def data_dashboard(request):
    est = pytz.timezone('America/New_York')
    events = Event.objects.all()

    # Group events by hour of the day and count them
    events_by_hour = (
        events
        .annotate(hour=ExtractHour('start_time'))
        .values('hour')
        .annotate(event_count=Count('id'))
        .order_by('hour')
    )

    # Convert event hours to EST
    for event in events_by_hour:
        start_time_utc = datetime.combine(
            datetime.now(), time(
                event['hour'])).replace(
            tzinfo=pytz.utc)
        start_time_est = start_time_utc.astimezone(est)
        event['hour'] = start_time_est.hour

    # Get categories with their associated hours
    events_with_categories = events.exclude(
        categories__isnull=True).exclude(
        categories__exact='')

    category_data = []
    for event in events_with_categories:
        hour = event.start_time.astimezone(est).hour
        categories = event.categories.strip("[]\"").split(",")
        for category in categories:
            # Convert to lowercase
            cleaned_category = category.strip().lower()
            # Replace non-alphanumeric characters with spaces and remove extra
            # spaces
            cleaned_category = re.sub(
                r'[^a-z0-9]+', ' ', cleaned_category).strip()
            category_data.append({
                'category': cleaned_category,
                'hour': hour
            })

    # Generate the initial Folium map with a heatmap layer
    map_html = generate_heatmap(events, est)

    context = {
        'events_by_hour': events_by_hour,
        'category_data': category_data,
        'map_html': map_html
    }
    return render(request, 'access_amherst_algo/dashboard.html', context)


def generate_heatmap(events, timezone, min_hour=None, max_hour=None):
    """Generate heatmap HTML based on filtered events within the specified time range."""
    if min_hour is not None and max_hour is not None:
        events = events.annotate(event_hour=ExtractHour('start_time')).filter(
            event_hour__gte=min_hour,
            event_hour__lte=max_hour
        )

    # Convert to local time for accurate filtering
    filtered_heatmap_data = [
        [float(event.latitude), float(event.longitude)]
        for event in events if event.latitude and event.longitude
    ]

    folium_map = folium.Map(
        location=[
            42.37284302722828, -72.51584816807264], zoom_start=17)
    if filtered_heatmap_data:
        HeatMap(filtered_heatmap_data).add_to(folium_map)

    return folium_map._repr_html_()


@csrf_exempt
def update_heatmap(request):
    """Update heatmap based on time range selected via sliders."""
    if request.method == "POST":
        data = json.loads(request.body)
        min_hour = data.get('min_hour', 7)
        max_hour = data.get('max_hour', 22)

        # Filter events by the selected time range and generate updated heatmap
        events = Event.objects.all()
        est = pytz.timezone('America/New_York')
        map_html = generate_heatmap(
            events, est, min_hour=min_hour, max_hour=max_hour)

        return JsonResponse({'map_html': map_html})
