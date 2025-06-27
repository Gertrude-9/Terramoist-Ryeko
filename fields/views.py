# fields/views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.gis.geos import Polygon
from .models import Field
from .utils import (
    FieldGeometryUtils,
    FieldSpatialOperations,
    IrrigationGDALOperations,
    SensorGDALOperations
)

class FieldValidationAPI(APIView):
    """API for validating field geometries"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            coordinates = request.data.get('coordinates')
            if not coordinates or len(coordinates) < 3:
                return Response(
                    {"error": "At least 3 coordinates are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            polygon = Polygon(coordinates)
            validation_results = FieldGeometryUtils.validate_field_polygon(polygon)
            
            return Response({
                "validation": validation_results,
                "area_acres": FieldGeometryUtils.calculate_field_area(polygon)
            })
        
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class FieldZoneDivisionAPI(APIView):
    """API for dividing fields into irrigation zones"""
    permission_classes = [IsAuthenticated]

    def post(self, request, field_id):
        try:
            field = Field.objects.get(pk=field_id, farm__owner=request.user)
            num_zones = request.data.get('num_zones', 4)
            
            zones = FieldSpatialOperations.split_field_into_zones(
                field.boundary, 
                int(num_zones)
            )

            return Response({
                "zones": [zone.coords for zone in zones],
                "zone_areas": [
                    FieldGeometryUtils.calculate_field_area(zone)
                    for zone in zones
                ]
            })
        
        except Field.DoesNotExist:
            return Response(
                {"error": "Field not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class FieldWaterRequirementsAPI(APIView):
    """API for calculating field water needs"""
    permission_classes = [IsAuthenticated]

    def get(self, request, field_id):
        try:
            field = Field.objects.get(pk=field_id, farm__owner=request.user)
            crop_coeff = float(request.query_params.get('crop_coefficient', 1.0))
            ref_et = float(request.query_params.get('reference_et', 5.0))
            
            water_needs = IrrigationGDALOperations.calculate_zone_water_needs(
                field.boundary,
                crop_coeff,
                ref_et
            )
            
            return Response(water_needs)
        
        except Field.DoesNotExist:
            return Response(
                {"error": "Field not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class FieldSensorCoverageAPI(APIView):
    """API for analyzing sensor coverage of a field"""
    permission_classes = [IsAuthenticated]

    def get(self, request, field_id):
        try:
            field = Field.objects.get(pk=field_id, farm__owner=request.user)
            sensors = field.sensors.all()
            
            coverage = SensorGDALOperations.check_zone_coverage_by_sensors(
                field.boundary,
                list(sensors)
            )
            
            return Response({
                "coverage": coverage,
                "optimal_placement": [
                    point.coords for point in 
                    SensorGDALOperations.optimize_sensor_placement(
                        field.boundary,
                        coverage_radius=100  # meters
                    )
                ]
            })
        
        except Field.DoesNotExist:
            return Response(
                {"error": "Field not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
