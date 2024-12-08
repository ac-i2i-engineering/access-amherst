from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.data_dashboard, name="dashboard"),
    path("map/", views.map_view, name="map"),
    path("update_heatmap/", views.update_heatmap, name="update_heatmap"),
    path('update_gantt/', views.update_gantt, name='update_gantt'),
    path("calendar/", views.calendar_view, name="calendar"),
    path('about/', views.about, name='about'),
]
