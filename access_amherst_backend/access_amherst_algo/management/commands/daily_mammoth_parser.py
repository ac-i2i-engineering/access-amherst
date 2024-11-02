from django.core.management.base import BaseCommand
from access_amherst_algo.email_scraper.email_parser import parse_email


class Command(BaseCommand):
    help = 'Parse the Daily Mammoth into a json'

    def handle(self, *args, **kwargs):
        parse_email(subject_filter="Daily Mammoth")
        self.stdout.write(self.style.SUCCESS(
            'Successfully parsed Daily Mammoth into json'))
