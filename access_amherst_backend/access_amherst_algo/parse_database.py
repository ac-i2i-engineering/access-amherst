from django.db.models import Count
from django.db.models.functions import ExtractHour
from .models import Event
from datetime import datetime
import re


def make_naive(event):
    """Ensure start_time and end_time are naive datetimes."""
    if event.start_time and event.start_time.tzinfo:
        event.start_time = event.start_time.replace(tzinfo=None)
    if event.end_time and event.end_time.tzinfo:
        event.end_time = event.end_time.replace(tzinfo=None)


def filter_events(query="", locations=None, start_date=None, end_date=None):
    """
    Filter events based on a search query, location, and date range.

    This function allows for filtering a list of events by title (via a search query), 
    location (by matching the event's map location), and a date range (by filtering 
    events that occur between the provided start and end dates). The function returns 
    a distinct set of events that match the provided criteria.
    """
    events = Event.objects.all()

    if query:
        events = events.filter(title__icontains=query)

    if locations:
        events = events.filter(map_location__in=locations)

    if start_date and end_date:
        events = events.filter(start_time__date__range=[start_date, end_date])

    for event in events:
        make_naive(event)

    return events.distinct()


def get_unique_locations():
    """
    Retrieve distinct event locations for filtering.

    This function queries the database to return a list of unique event locations 
    from the `map_location` field, which can be used for filtering events based on 
    location.
    """
    return Event.objects.values_list("map_location", flat=True).distinct()


def get_events_by_hour(events):
    """
    Group events by the hour with naive datetime adjustment.

    Parameters
    ----------
    events : QuerySet
        A queryset containing event data, which should include a `start_time` field.

    Returns
    -------
    list
        A list of dictionaries, each containing the hour and event count.
    """
    for event in events:
        make_naive(event)

    events_by_hour = (
        events.exclude(start_time__isnull=True)
        .annotate(hour=ExtractHour("start_time"))
        .values("hour")
        .annotate(event_count=Count("id"))
        .order_by("hour")
    )

    return events_by_hour


def get_category_data(events):
    """
    Parse and clean category data for events, grouping by hour with naive datetime adjustment.

    Parameters
    ----------
    events : QuerySet
        A queryset containing event data with `start_time` and `categories` fields.

    Returns
    -------
    list
        A list of dictionaries with cleaned category and corresponding event hour.
    """
    category_data = []
    events = events.exclude(start_time__isnull=True)

    for event in events:
        make_naive(event)

        if event.start_time:
            hour = event.start_time.hour  # Direct hour access without timezone conversion
            categories = event.categories.strip('[]"').split(",")

            for category in categories:
                cleaned_category = re.sub(
                    r"[^a-z0-9]+", " ", category.strip().lower()
                ).strip()
                category_data.append(
                    {"category": cleaned_category, "hour": hour}
                )

    return category_data


def filter_events_by_category(events, categories):
    """
    Filter events by a list of categories.

    Parameters
    ----------
    events : QuerySet
        A queryset containing event data.
    categories : list of str
        A list of categories to filter events.

    Returns
    -------
    QuerySet
        A queryset of events matching the provided categories.
    """
    if categories:
        category_regex = "|".join(re.escape(cat) for cat in categories)
        events = events.filter(categories__iregex=rf"(\b{category_regex}\b)")

    for event in events:
        make_naive(event)

    return events


def clean_category(category):
    """
    Clean a category string to ensure it starts and ends with alphanumeric characters.

    Parameters
    ----------
    category : str
        The category string to clean.

    Returns
    -------
    str
        The cleaned category string.
    """
    return re.sub(r"^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$", "", category.strip())


def get_unique_categories():
    """
    Retrieve unique categories from events, ensuring they start and end with alphanumeric characters.

    Returns
    -------
    list
        A list of unique, cleaned categories.
    """
    categories = Event.objects.values_list("categories", flat=True)
    unique_categories = set()
    for category_list in categories:
        if category_list:
            unique_categories.update(
                clean_category(category) for category in category_list.split(",")
            )
    return sorted(unique_categories)