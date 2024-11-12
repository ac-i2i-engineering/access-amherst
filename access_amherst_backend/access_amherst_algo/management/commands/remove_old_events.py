from django.core.management.base import BaseCommand
from django.utils import timezone
from access_amherst_algo.models import Event


class Command(BaseCommand):
    help = "Deletes events that have a start_time older than 24 hours"

    def handle(self, *args, **kwargs):
        threshold_time = timezone.now() - timezone.timedelta(hours=2)
        deleted_count, _ = Event.objects.filter(
            start_time__lt=threshold_time
        ).delete()
        self.stdout.write(
            self.style.SUCCESS(f"Deleted {deleted_count} old event(s).")
        )
