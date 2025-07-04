# Generated by Django 4.2 on 2025-06-30 16:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("fields", "0002_alter_farm_owner"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="sensor",
            options={"ordering": ["name", "field"]},
        ),
        migrations.RenameField(
            model_name="sensor",
            old_name="installed_date",
            new_name="installation_date",
        ),
        migrations.AlterUniqueTogether(
            name="sensor",
            unique_together=set(),
        ),
        migrations.AddField(
            model_name="field",
            name="area",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="Field area in hectares",
                max_digits=10,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="field",
            name="description",
            field=models.TextField(
                blank=True,
                help_text="Additional notes or description about this field",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="field",
            name="geometry",
            field=models.TextField(
                blank=True,
                help_text="GeoJSON or other spatial data representing the field boundary",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="field",
            name="irrigation_system",
            field=models.CharField(
                blank=True,
                choices=[
                    ("DRIP", "Drip Irrigation"),
                    ("SPRINKLER", "Sprinkler System"),
                    ("FLOOD", "Flood Irrigation"),
                    ("NONE", "None"),
                ],
                help_text="Type of irrigation system used",
                max_length=50,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="field",
            name="is_active",
            field=models.BooleanField(
                default=True,
                help_text="Check if this field is currently active for monitoring",
            ),
        ),
        migrations.AddField(
            model_name="field",
            name="latitude",
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                help_text="GPS latitude coordinate",
                max_digits=9,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="field",
            name="longitude",
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                help_text="GPS longitude coordinate",
                max_digits=9,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="field",
            name="planting_date",
            field=models.DateField(
                blank=True,
                help_text="Date when crops were planted in this field",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="field",
            name="soil_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("SANDY", "Sandy"),
                    ("CLAY", "Clay"),
                    ("LOAM", "Loam"),
                    ("SILT", "Silt"),
                    ("PEAT", "Peat"),
                    ("CHALKY", "Chalky"),
                ],
                help_text="Predominant soil type in this field",
                max_length=50,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="sensor",
            name="battery_level",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="Current battery level (%)",
                max_digits=5,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="sensor",
            name="calibration_offset",
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                help_text="Offset value for sensor calibration (c in y=mx+c)",
                max_digits=10,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="sensor",
            name="calibration_slope",
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                help_text="Slope value for sensor calibration (m in y=mx+c)",
                max_digits=10,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="sensor",
            name="depth",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="Depth of sensor installation (e.g., in cm or inches)",
                max_digits=5,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="sensor",
            name="description",
            field=models.TextField(
                blank=True,
                help_text="Additional notes or description about the sensor",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="sensor",
            name="device_id",
            field=models.CharField(
                blank=True,
                help_text="Unique identifier for the physical sensor device",
                max_length=100,
                null=True,
                unique=True,
            ),
        ),
        migrations.AddField(
            model_name="sensor",
            name="last_calibration",
            field=models.DateField(
                blank=True, help_text="Date of the last sensor calibration", null=True
            ),
        ),
        migrations.AddField(
            model_name="sensor",
            name="latitude",
            field=models.DecimalField(
                decimal_places=6,
                default=0.0,
                help_text="GPS latitude of sensor position",
                max_digits=10,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="sensor",
            name="longitude",
            field=models.DecimalField(
                decimal_places=6,
                default=0.0,
                help_text="GPS longitude of sensor position",
                max_digits=10,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="sensor",
            name="name",
            field=models.CharField(
                blank=True,
                help_text="A unique name for the sensor",
                max_length=100,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="sensor",
            name="reading_frequency",
            field=models.IntegerField(
                blank=True,
                help_text="Frequency of readings in minutes (e.g., 60 for hourly)",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="sensor",
            name="status",
            field=models.CharField(
                choices=[
                    ("active", "Active"),
                    ("inactive", "Inactive"),
                    ("maintenance", "Under Maintenance"),
                    ("faulty", "Faulty"),
                ],
                default="active",
                help_text="Current operational status of the sensor",
                max_length=20,
            ),
        ),
        migrations.AlterUniqueTogether(
            name="field",
            unique_together={("farm", "name")},
        ),
        migrations.AlterUniqueTogether(
            name="sensor",
            unique_together={("field", "latitude", "longitude")},
        ),
        migrations.RemoveField(
            model_name="field",
            name="area_hectares",
        ),
        migrations.RemoveField(
            model_name="sensor",
            name="position_x",
        ),
        migrations.RemoveField(
            model_name="sensor",
            name="position_y",
        ),
    ]
