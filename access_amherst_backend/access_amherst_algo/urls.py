from django.urls import path
from . import views

urlpatterns = [
    path(
        '',
        views.home,
        name='home'),
    path(
        'dashboard/',
        views.data_dashboard,
        name='dashboard'),
    path(
        'map/',
        views.map_view,
        name='map'),
    path(
        'update_heatmap/',
        views.update_heatmap,
        name='update_heatmap'),
    path(
        'run_db_saver/',
        views.run_db_saver,
        name='run_db_saver'),
    path(
        'run_events_list_creator/',
        views.run_events_list_creator,
        name='run_events_list_creator'),
    path(
        'run_json_saver/',
        views.run_json_saver,
        name='run_json_saver'),
    path(
        'run_rss_fetcher/',
        views.run_rss_fetcher,
        name='run_rss_fetcher'),
    path(
        'run_hub_data_cleaner/',
        views.run_hub_data_cleaner,
        name='run_hub_data_cleaner'),
]
