from django.core.management.base import BaseCommand
from django.utils import timezone
from access_amherst_algo.models import Event

class Command(BaseCommand):
    help = "Deletes events that have a start_time older than 24 hours"

    def handle(self, *args, **kwargs):
        threshold_time = timezone.now() - timezone.timedelta(hours=2)
        old_events = Event.objects.filter(start_time__lt=threshold_time)
        
        # Log each event that will be deleted
        for event in old_events:
            self.stdout.write(
                self.style.WARNING(f"Deleting event: ID={event.id}, Name={event.name}, Start Time={event.start_time}, Link={event.link}")
            )
        
        # Perform the deletion and log the count of deleted events
        deleted_count, _ = old_events.delete()
        self.stdout.write(
            self.style.SUCCESS(f"Deleted {deleted_count} old event(s).")
        )
