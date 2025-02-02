# generate_map.py
import folium
from folium.plugins import HeatMap
from django.db.models.functions import ExtractHour
import urllib.parse
from datetime import datetime
import pytz


def create_map(center_coords, zoom_start=17):
    """
    Initialize a Folium map centered around the specified coordinates.

    This function creates and returns a Folium map centered on the provided 
    latitude and longitude coordinates. The zoom level can be adjusted, with 
    a default zoom level of 17 for close-up views.

    Parameters
    ----------
    center_coords : tuple of float
        A tuple specifying the latitude and longitude (in that order) for the 
        center of the map.
    zoom_start : int, default 17
        The initial zoom level of the map, where higher values provide a 
        closer view.

    Returns
    -------
    folium.Map
        A Folium map object centered on the specified coordinates and set to 
        the defined zoom level.

    Examples
    --------
    >>> map_object = create_map((42.37284302722828, -72.51584816807264))
    """
    return folium.Map(location=center_coords, zoom_start=zoom_start)


def add_event_markers(folium_map, events):
    """
    Add event markers to a Folium map with popups and Google Calendar links.

    This function takes a Folium map and a list of event data to add interactive markers 
    representing each event. Each marker includes a popup displaying event details 
    (title, location, start and end times) and a link to add the event to Google Calendar.

    Parameters
    ----------
    folium_map : folium.Map
        The Folium map object where the event markers will be added.
    events : list of Event
        A list of Event objects containing event details such as title, start and end times, 
        location, description, and map coordinates (latitude and longitude).

    Returns
    -------
    folium.Map
        The Folium map object with added markers for each event.

    Examples
    --------
    >>> map_object = create_map((42.37284302722828, -72.51584816807264))
    >>> events = [
    >>>     Event(
    >>>         title="Literature Speaker Event",
    >>>         start_time=datetime(2024, 11, 5, 18, 0),
    >>>         end_time=datetime(2024, 11, 5, 20, 0),
    >>>         location="Keefe Campus Center",
    >>>         map_location="Amherst, MA",
    >>>         latitude=42.37149564586236,
    >>>         longitude=-72.51478632450079,
    >>>         event_description="Join us to hear our speaker's talk on American Literature! Food from a local restaurant will be provided."
    >>>     )
    >>> ]
    >>> add_event_markers(map_object, events)
    """
    for event in events:
        start_time = event.start_time.strftime("%Y-%m-%d %H:%M")
        end_time = event.end_time.strftime("%Y-%m-%d %H:%M")

        google_calendar_link = (
            "https://www.google.com/calendar/render?action=TEMPLATE"
            f"&text={urllib.parse.quote(event.title)}"
            f"&dates={event.start_time.strftime('%Y%m%dT%H%M%SZ')}/{event.end_time.strftime('%Y%m%dT%H%M%SZ')}"
            f"&details={urllib.parse.quote(event.event_description)}"
            f"&location={urllib.parse.quote(event.location)}"
        )

        popup_html = (
            f"<strong>{event.title}</strong><br>"
            f"{event.location} ({event.map_location})<br>"
            f"Start: {start_time}<br>"
            f"End: {end_time}<br>"
            f"<a href='{google_calendar_link}' target='_blank'>Add to Google Calendar</a>"
        )

        folium.Marker(
            location=[float(event.latitude), float(event.longitude)],
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(color="blue", icon="info-sign"),
        ).add_to(folium_map)

    return folium_map


def generate_heatmap(events, timezone, min_hour=None, max_hour=None):
    """
    Generate a heatmap map object based on filtered events within a specified time range.

    This function filters events based on the provided time range (specified by `min_hour` 
    and `max_hour`, if provided) and generates a heatmap of event locations using their 
    geographical coordinates (latitude and longitude). The heatmap is then added to a 
    Folium map, which is returned for further use.

    Parameters
    ----------
    events : QuerySet
        A QuerySet of Event objects, each containing attributes like latitude, longitude, 
        and start time.
    timezone : pytz.timezone
        The timezone used for filtering events based on their start times.
    min_hour : int, optional
        The minimum hour (0-23) of the day to filter events by start time. Default is None.
    max_hour : int, optional
        The maximum hour (0-23) of the day to filter events by start time. Default is None.

    Returns
    -------
    folium.Map
        The Folium map object with a heatmap layer representing event locations within 
        the specified time range.

    Examples
    --------
    >>> events = Event.objects.all()  # Example QuerySet of events
    >>> timezone = pytz.timezone('America/New_York')
    >>> folium_map = generate_heatmap(events, timezone, min_hour=9, max_hour=17)
    >>> folium_map.save("events_heatmap.html")  # Saves the map with heatmap to an HTML file
    """
    if min_hour is not None and max_hour is not None:
        # Convert user-specified hours to UTC for database query
        min_hour = datetime(1970, 1, 1, min_hour, 0, tzinfo=timezone).astimezone(pytz.utc).hour
        max_hour = datetime(1970, 1, 1, max_hour, 59, tzinfo=timezone).astimezone(pytz.utc).hour

        events = events.annotate(event_hour=ExtractHour("start_time")).filter(
            event_hour__gte=min_hour, event_hour__lte=max_hour
        )

    heatmap_data = [
        [float(event.latitude), float(event.longitude)]
        for event in events
        if event.latitude and event.longitude
    ]

    folium_map = folium.Map(
        location=[42.37284302722828, -72.51584816807264], zoom_start=17
    )
    if heatmap_data:
        HeatMap(heatmap_data).add_to(folium_map)

    return folium_map
