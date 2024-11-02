from django.core.management.base import BaseCommand
from access_amherst_algo.rss_scraper.parse_rss import save_to_db


class Command(BaseCommand):
    help = 'Saves parsed RSS events and saves to DB'

    def handle(self, *args, **kwargs):
        save_to_db()
        self.stdout.write(self.style.SUCCESS(
            'Successfully saved parsed RSS events to DB'))
