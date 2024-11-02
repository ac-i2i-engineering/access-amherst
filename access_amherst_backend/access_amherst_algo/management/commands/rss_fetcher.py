from django.core.management.base import BaseCommand
from access_amherst_algo.rss_scraper.fetch_rss import fetch_rss


class Command(BaseCommand):
    help = 'Fetches the RSS feed from the Amherst Hub'

    def handle(self, *args, **kwargs):
        fetch_rss()
        self.stdout.write(self.style.SUCCESS(
            'Successfully fetched the RSS feed from the Amherst Hub'))
