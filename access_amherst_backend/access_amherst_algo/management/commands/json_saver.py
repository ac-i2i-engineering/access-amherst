from django.core.management.base import BaseCommand
from access_amherst_algo.rss_scraper.parse_rss import save_json


class Command(BaseCommand):
    help = 'Saves parsed RSS events into json file'

    def handle(self, *args, **kwargs):
        save_json()
        self.stdout.write(self.style.SUCCESS(
            'Successfully saved parsed RSS events to json'))
