from django.core.management.base import BaseCommand
from access_amherst_algo.rss_scraper.clean_hub_data import clean_hub_data


class Command(BaseCommand):
    help = 'Cleans hub data'

    def handle(self, *args, **kwargs):
        clean_hub_data()
        self.stdout.write(self.style.SUCCESS('Successfully cleaned hub data'))
