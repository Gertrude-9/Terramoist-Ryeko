# Generated by Django 5.2.3 on 2025-07-09 16:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Field",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("location", models.CharField(max_length=100)),
                ("area", models.FloatField(help_text="Area in hectares")),
                ("crop_type", models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name="IrrigationLog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("start_time", models.DateTimeField()),
                ("end_time", models.DateTimeField(blank=True, null=True)),
                (
                    "duration",
                    models.PositiveIntegerField(
                        blank=True, help_text="Actual duration in minutes", null=True
                    ),
                ),
                (
                    "water_used",
                    models.FloatField(
                        blank=True, help_text="Water used in liters", null=True
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("running", "Running"),
                            ("completed", "Completed"),
                            ("skipped", "Skipped"),
                            ("failed", "Failed"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("reason", models.TextField(blank=True)),
                (
                    "field",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="irrigation.field",
                    ),
                ),
            ],
            options={
                "ordering": ["-start_time"],
            },
        ),
        migrations.CreateModel(
            name="IrrigationSchedule",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("start_time", models.TimeField()),
                (
                    "duration",
                    models.PositiveIntegerField(help_text="Duration in minutes"),
                ),
                (
                    "frequency",
                    models.CharField(
                        choices=[
                            ("daily", "Daily"),
                            ("weekly", "Weekly"),
                            ("custom", "Custom"),
                        ],
                        max_length=20,
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("last_run", models.DateTimeField(blank=True, null=True)),
                (
                    "field",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="irrigation.field",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="IrrigationZone",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("area", models.FloatField(help_text="Area in square meters")),
                ("crop_type", models.CharField(max_length=100)),
                (
                    "field",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="zones",
                        to="irrigation.field",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Sensor",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "sensor_type",
                    models.CharField(
                        choices=[
                            ("soil_moisture", "Soil Moisture"),
                            ("temperature", "Temperature"),
                            ("humidity", "Humidity"),
                        ],
                        max_length=20,
                    ),
                ),
                ("installation_date", models.DateField()),
                ("is_active", models.BooleanField(default=True)),
                (
                    "field",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sensors",
                        to="irrigation.field",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="SensorReading",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("value", models.FloatField()),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                (
                    "sensor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="irrigation.sensor",
                    ),
                ),
            ],
            options={
                "ordering": ["-timestamp"],
            },
        ),
        migrations.CreateModel(
            name="WeatherData",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("temperature", models.FloatField()),
                ("humidity", models.FloatField()),
                ("rainfall", models.FloatField(help_text="Rainfall in mm")),
                ("wind_speed", models.FloatField()),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                (
                    "field",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="irrigation.field",
                    ),
                ),
            ],
            options={
                "ordering": ["-timestamp"],
            },
        ),
    ]
