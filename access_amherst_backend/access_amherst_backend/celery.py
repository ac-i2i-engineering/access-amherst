from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set the default Django settings module
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "access_amherst_backend.settings"
)

# Initialize Celery
app = Celery("access_amherst_backend")

# Load settings from Django settings.py
app.config_from_object("django.conf:settings", namespace="CELERY")

# Setup Django first
import django

django.setup()

# Now import models after Django is setup
from django_celery_beat.models import (
    PeriodicTask,
    IntervalSchedule,
    CrontabSchedule,
)

# Auto-discover tasks in all registered Django apps
app.autodiscover_tasks()


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    """
    Setup periodic tasks for Celery Beat.
    """
    # Clear existing tasks
    PeriodicTask.objects.filter(
        name__in=[
            "Initiate Hub Workflow",
            "Initiate Daily Mammoth Workflow",
            "Remove Old Events",
        ]
    ).delete()

    # 6-hour interval task
    interval_schedule, _ = IntervalSchedule.objects.get_or_create(
        every=10, period=IntervalSchedule.minute
    )
    PeriodicTask.objects.create(
        interval=interval_schedule,
        name="Initiate Hub Workflow",
        task="access_amherst_algo.tasks.initiate_hub_workflow",
    )

    # Daily Mammoth task at 8:30 AM EST
    crontab_schedule_daily_mammoth, _ = CrontabSchedule.objects.get_or_create(
        minute="30",
        hour="16",
        day_of_week="*",
        day_of_month="*",
        month_of_year="*",
        timezone="America/New_York",
    )
    PeriodicTask.objects.create(
        crontab=crontab_schedule_daily_mammoth,
        name="Initiate Daily Mammoth Workflow",
        task="access_amherst_algo.tasks.initiate_daily_mammoth_workflow",
    )

    # Remove old events at 10 PM EST
    crontab_schedule_remove_old, _ = CrontabSchedule.objects.get_or_create(
        minute="0",
        hour="3",
        day_of_week="*",
        day_of_month="*",
        month_of_year="*",
        timezone="America/New_York",
    )
    PeriodicTask.objects.create(
        crontab=crontab_schedule_remove_old,
        name="Remove Old Events",
        task="access_amherst_algo.tasks.remove_old_events",
    )
