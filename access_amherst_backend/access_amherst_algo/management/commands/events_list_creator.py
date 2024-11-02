from django.core.management.base import BaseCommand
from access_amherst_algo.rss_scraper.parse_rss import create_events_list


class Command(BaseCommand):
    help = 'creates events list after parsing RSS events'

    def handle(self, *args, **kwargs):
        create_events_list()
        self.stdout.write(self.style.SUCCESS(
            'Successfully created events list'))
