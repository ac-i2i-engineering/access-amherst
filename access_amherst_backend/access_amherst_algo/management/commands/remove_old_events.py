from django.core.management.base import BaseCommand
from django.utils import timezone
from access_amherst_algo.models import Event
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Deletes events that have a start_time older than 2 hours"

    def handle(self, *args, **kwargs):
        threshold_time = timezone.now() - timezone.timedelta(hours=2)
        old_events = Event.objects.filter(start_time__lt=threshold_time)
        
        deleted_count, _ = old_events.delete()
        
        for event in old_events:
            logger.info(f"Deleted event: ID={event.id}, Name={event.name}, Start Time={event.start_time}, Link={event.link}")

        self.stdout.write(
            self.style.SUCCESS(f"Deleted {deleted_count} old event(s).")
        )
