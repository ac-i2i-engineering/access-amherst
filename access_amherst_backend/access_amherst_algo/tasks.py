from celery import shared_task
from django.core.management import call_command


@shared_task
def remove_old_events():
    call_command('remove_old_events')
