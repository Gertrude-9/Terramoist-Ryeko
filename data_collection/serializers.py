# serializers.py
from rest_framework import serializers
from .models import SensorData

class SensorDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorData
        fields = ['sensor_id', 'value', 'timestamp']
        extra_kwargs = {
            'sensor_id': {'write_only': True},
            'timestamp': {'read_only': True}
        }