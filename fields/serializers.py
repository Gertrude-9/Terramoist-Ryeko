from rest_framework import serializers
from .models import Field, Sensor

class FieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = Field
        fields = ['id', 'name', 'farm', 'crop_type', 'area', 'soil_type', 'boundary']

class SensorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sensor
        fields = ['id', 'name', 'field', 'sensor_type', 'status', 'location', 'last_reading']