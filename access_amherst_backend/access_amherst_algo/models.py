from django.db import models


class Event(models.Model):
    """
    Event model representing an event with various attributes such as title, description, time, 
    location, and associated metadata. This class stores the details of an event and includes 
    fields for the event's author, start and end times, location, and categories. It also provides 
    methods for querying and manipulating event data.

    Parameters
    ----------
    id : int
        A unique identifier for the event (primary key).
    title : str
        The title of the event.
    author_name : str, optional
        The name of the author of the event.
    author_email : str, optional
        The email address of the author of the event.
    pub_date : datetime, optional
        The publication date of the event.
    host : str, optional
        A comma-separated list or JSON of hosts for the event.
    link : str, optional
        A URL link related to the event (e.g., a registration page or event page).
    picture_link : str, optional
        A URL link to an image representing the event.
    event_description : str, optional
        A detailed description of the event.
    start_time : datetime, optional
        The start time of the event.
    end_time : datetime, optional
        The end time of the event.
    location : str, optional
        The location of the event.
    categories : str
        A comma-separated list or JSON of categories the event belongs to.
    latitude : float, optional
        The latitude of the event location.
    longitude : float, optional
        The longitude of the event location.
    map_location : str, optional
        A textual description of the location on a map.

    Methods
    -------
    __str__() :
        Returns a string representation of the event (the event's title).
    """
    id = models.IntegerField(
        primary_key=True, unique=True, null=False, blank=False
    )
    title = models.CharField(max_length=255)
    author_name = models.CharField(max_length=255, null=True, blank=True)
    author_email = models.CharField(max_length=255, null=True, blank=True)
    pub_date = models.DateTimeField(null=True, blank=True)
    host = models.TextField(
        null=True, blank=True
    )  # This can store a list of hosts as a comma-separated string or JSON
    link = models.URLField(max_length=500, null=True, blank=True)
    picture_link = models.URLField(max_length=500, null=True, blank=True)
    event_description = models.TextField(null=True, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=500, null=True, blank=True)
    categories = (
        models.TextField()
    )  # This can store a list of categories as a comma-separated string or JSON
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    map_location = models.CharField(max_length=500, null=True)
    
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

    @property
    def emojis(self):
        if isinstance(self.categories, str):
            categories_str = self.categories.strip('[]')
            categories_list = [cat.strip().strip('"\'') for cat in categories_str.split(',') if cat.strip()]
        else:
            categories_list = self.categories
        return [self.CATEGORY_EMOJI_MAP.get(category, " 🗓️ ") for category in categories_list]

    def __str__(self):
        return self.title
