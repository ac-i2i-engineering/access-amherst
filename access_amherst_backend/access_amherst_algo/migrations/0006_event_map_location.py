# Generated by Django 5.1.1 on 2024-10-31 22:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("access_amherst_algo", "0005_event_latitude_event_longitude"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="map_location",
            field=models.CharField(max_length=500, null=True),
        ),
    ]
