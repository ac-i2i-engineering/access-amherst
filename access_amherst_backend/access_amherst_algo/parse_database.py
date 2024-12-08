from django.db.models import Count, F
from django.db.models.functions import ExtractHour
from .models import Event
from datetime import datetime, time
import pytz
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List


def filter_events(query="", locations=None, start_date=None, end_date=None, similarity_threshold=0.1):
    """
    Filter events based on a search query, location, and date range.

    This function allows for filtering a list of events by title (via a search query), 
    location (by matching the event's map location), and a date range (by filtering 
    events that occur between the provided start and end dates). The function returns 
    a distinct set of events that match the provided criteria.

    Parameters
    ----------
    query : str, optional
        The search query to filter event titles. The default is an empty string, which 
        will not filter by title.
    locations : list of str, optional
        A list of locations to filter events by their map location. The default is None, 
        meaning no location filter is applied.
    start_date : date, optional
        The start date to filter events by their start time. The default is None.
    end_date : date, optional
        The end date to filter events by their start time. The default is None.
    similarity_threshold : float, optional
        The cosine similarity threshold for filtering events by title. The default is 0.1.

    Returns
    -------
    QuerySet
        A QuerySet of distinct events that match the specified filters.

    Examples
    --------
    >>> events = filter_events(query="Speaker", locations=["Keefe Campus Center"], 
    >>>                         start_date="2024-11-01", end_date="2024-11-30")
    >>> for event in events:
    >>>     print(event.title)
    """
    events = Event.objects.all()
    
    # Apply location and date filters
    if locations:
        events = events.filter(map_location__in=locations)
    if start_date and end_date:
        events = events.filter(start_time__date__range=[start_date, end_date])

    if not query:
        return events.order_by('start_time').distinct()

    # Get exact matches first (case insensitive)
    exact_matches = events.filter(title__icontains=query)
    
    # Get similarity matches
    event_list = list(events.exclude(id__in=exact_matches.values_list('id', flat=True)))
    if not event_list:
        return exact_matches
        
    titles = [preprocess_text(event.title) for event in event_list]
    processed_query = preprocess_text(query)
    
    # Get similarity scores
    similarity_scores = compute_similarity_scores(processed_query, titles)
    
    # Create and filter (event_id, score) pairs
    event_scores = [
        (event.id, score) 
        for event, score in zip(event_list, similarity_scores)
        if score >= similarity_threshold
    ]
    
    if not event_scores:
        return exact_matches
        
    # Prepare similarity cases for both exact and fuzzy matches
    from django.db.models import Case, When, FloatField, Value

    # Give exact matches a similarity score of 1.0
    exact_scores = [(event.id, 1.0) for event in exact_matches]
    all_scores = exact_scores + event_scores
    
    score_cases = [
        When(pk=event_id, then=Value(score))
        for event_id, score in all_scores
    ]
    
    # Combine results with similarity annotations
    return (Event.objects
           .filter(id__in=[id for id, _ in all_scores])
           .annotate(
               similarity=Case(
                   *score_cases,
                   default=0.0,
                   output_field=FloatField(),
               )
           )
           .order_by('-similarity'))


def preprocess_text(text: str) -> str:
    """Clean and normalize text for comparison."""
    # Convert to lowercase and remove special characters
    text = re.sub(r'[^\w\s]', '', text.lower())
    return text.strip()


def compute_similarity_scores(query: str, titles: List[str]) -> List[float]:
    """Compute cosine similarity between query and titles."""
    if not query or not titles:
        return [0] * len(titles)
    
    # Initialize TF-IDF vectorizer
    vectorizer = TfidfVectorizer(stop_words='english')
    
    # Combine query and titles for vectorization
    all_texts = [query] + titles
    
    # Create TF-IDF matrix
    tfidf_matrix = vectorizer.fit_transform(all_texts)
    
    # Compute cosine similarity between query and each title
    similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
    
    return similarities[0]


def get_unique_locations():
    """
    Retrieve distinct event locations for filtering.

    This function queries the database to return a list of unique event locations 
    from the `map_location` field, which can be used for filtering events based on 
    location.

    Returns
    -------
    list
        A list of distinct event locations.

    Examples
    --------
    >>> locations = get_unique_locations()
    >>> print(locations)
    ['Keefe Campus Center', 'Science Center', ' Frost Library']
    """
    return Event.objects.values_list("map_location", flat=True).distinct()


def get_events_by_hour(events, timezone):
    """
    Group events by the hour and adjust to specified timezone.

    This function groups events based on the hour of their start time and adjusts 
    the hour to the specified timezone. It excludes events with null start times, 
    annotates each event with the hour of the start time, and counts the number of 
    events in each hour. The final result is a list of event counts by hour, with 
    the hour adjusted to the provided timezone.

    Parameters
    ----------
    events : QuerySet
        A queryset containing event data, which should include a `start_time` field.
    timezone : pytz.timezone
        The timezone to which the event hours should be adjusted.

    Returns
    -------
    list
        A list of dictionaries, each containing the hour and the corresponding event count.

    Examples
    --------
    >>> events_by_hour = get_events_by_hour(events, pytz.timezone("America/New_York"))
    >>> for event in events_by_hour:
    >>>     print(event)
    {'hour': 18, 'event_count': 5}
    {'hour': 19, 'event_count': 3}
    """
    events_by_hour = (
        events.exclude(
            start_time__isnull=True
        )
        .annotate(
            # Extract hour after converting to target timezone
            hour=ExtractHour(
                F('start_time'), 
                tzinfo=timezone
            )
        )
        .values('hour')
        .annotate(event_count=Count('id'))
        .order_by('hour')
    )
    
    return events_by_hour


def get_category_data(events, timezone):
    """
    Parse and clean category data for events, grouping by hour.

    This function processes a list of events, extracting and cleaning category 
    data for each event. It filters out events with null start times, converts 
    the event start times to the specified timezone, and then parses and normalizes 
    the categories associated with each event. The data is returned as a list of 
    dictionaries, each containing the cleaned category and the corresponding event hour.

    Parameters
    ----------
    events : QuerySet
        A queryset containing event data, which should include `start_time` and `categories` fields.
    timezone : pytz.timezone
        The timezone to which the event start times should be adjusted.

    Returns
    -------
    list
        A list of dictionaries, each containing the cleaned category and corresponding event hour.

    Examples
    --------
    >>> category_data = get_category_data(events, pytz.timezone("America/New_York"))
    >>> for category in category_data:
    >>>     print(category)
    {'category': 'Lecture', 'hour': 18}
    {'category': 'Workshop', 'hour': 19}
    """
    category_data = []

    # Filter out events with null start_time
    events = events.exclude(start_time__isnull=True)

    for event in events:
        if event.start_time:  # Ensure start_time is not None
            hour = event.start_time.astimezone(timezone).hour
            categories = event.categories.strip('[]"').split(",")

            for category in categories:
                cleaned_category = re.sub(
                    r"[^a-z0-9]+", " ", category.strip().lower()
                ).strip()
                category_data.append(
                    {"category": cleaned_category, "hour": hour}
                )
        else:
            # Optionally log or handle events with missing start_time
            pass

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