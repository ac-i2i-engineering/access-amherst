# FILE: access_amherst_backend/access_amherst_tests/test_views.py

import pytest
from django.urls import reverse
from django.test import Client
from django.utils import timezone
from access_amherst_algo.models import Event


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def create_events():
    Event.objects.create(
        title="Event 1",
        start_time=timezone.now(),
        end_time=timezone.now() + timezone.timedelta(hours=1),
        location="Location 1",
        map_location="Map Location 1",
        latitude=42.373611,
        longitude=-72.519444,
        event_description="Description 1",
        categories='["Category1"]'
    )
    Event.objects.create(
        title="Event 2",
        start_time=timezone.now(),
        end_time=timezone.now() + timezone.timedelta(hours=2),
        location="Location 2",
        map_location="Map Location 2",
        latitude=42.374611,
        longitude=-72.518444,
        event_description="Description 2",
        categories='["Category2"]'
    )


def test_run_rss_fetcher(client):
    response = client.get(reverse('run_rss_fetcher'))
    assert response.status_code == 302
    assert response.url == '../'


def test_run_hub_data_cleaner(client):
    response = client.get(reverse('run_hub_data_cleaner'))
    assert response.status_code == 302
    assert response.url == '../'
