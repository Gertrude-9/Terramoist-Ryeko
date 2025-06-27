"""
GDAL Helper functions for Farm Management Models
Provides spatial operations, conversions, and analysis for Farm, Field, Sensor, IrrigationZone, and WeatherStation models
"""

from django.contrib.gis.gdal import GDALRaster, OGRGeometry, SpatialReference, CoordTransform
from django.contrib.gis.geos import GEOSGeometry, Point, Polygon
from django.contrib.gis.measure import Area, Distance
import json
import math
from typing import List, Dict, Tuple, Optional, Union


class GDALFarmHelpers:
    """Helper class for GDAL operations on farm-related models"""
    
    @staticmethod
    def create_point_from_coords(lat: float, lng: float, srid: int = 4326) -> Point:
        """Create a Point geometry from latitude and longitude"""
        return Point(lng, lat, srid=srid)
    
    @staticmethod
    def create_polygon_from_coords(coordinates: List[List[float]], srid: int = 4326) -> Polygon:
        """
        Create a Polygon from coordinate list
        coordinates: List of [lng, lat] pairs forming the polygon boundary
        """
        if len(coordinates) < 3:
            raise ValueError("Polygon requires at least 3 coordinates")
        
        # Ensure polygon is closed
        if coordinates[0] != coordinates[-1]:
            coordinates.append(coordinates[0])
        
        return Polygon(coordinates, srid=srid)
    
    @staticmethod
    def transform_geometry(geometry: GEOSGeometry, target_srid: int) -> GEOSGeometry:
        """Transform geometry to different coordinate system"""
        if geometry.srid != target_srid:
            geometry.transform(target_srid)
        return geometry
    
    @staticmethod
    def calculate_accurate_area(geometry: GEOSGeometry, unit: str = 'acres') -> float:
        """
        Calculate accurate area using appropriate projection
        unit: 'acres', 'hectares', 'sq_meters', 'sq_km'
        """
        # Transform to UTM for accurate area calculation
        utm_srid = GDALFarmHelpers._get_utm_srid(geometry)
        transformed_geom = geometry.clone()
        transformed_geom.transform(utm_srid)
        
        area_sq_meters = transformed_geom.area
        
        conversions = {
            'sq_meters': 1,
            'hectares': 0.0001,
            'acres': 0.000247105,
            'sq_km': 0.000001
        }
        
        return area_sq_meters * conversions.get(unit, 1)
    
    @staticmethod
    def calculate_distance(point1: Point, point2: Point, unit: str = 'meters') -> float:
        """Calculate distance between two points"""
        # Transform to UTM for accurate distance calculation
        utm_srid = GDALFarmHelpers._get_utm_srid(point1)
        
        p1_utm = point1.clone()
        p2_utm = point2.clone()
        
        p1_utm.transform(utm_srid)
        p2_utm.transform(utm_srid)
        
        distance_meters = p1_utm.distance(p2_utm)
        
        conversions = {
            'meters': 1,
            'kilometers': 0.001,
            'feet': 3.28084,
            'miles': 0.000621371
        }
        
        return distance_meters * conversions.get(unit, 1)
    
    @staticmethod
    def _get_utm_srid(geometry: GEOSGeometry) -> int:
        """Get appropriate UTM SRID for geometry"""
        centroid = geometry.centroid
        lng = centroid.x
        lat = centroid.y
        
        # Calculate UTM zone
        utm_zone = int((lng + 180) / 6) + 1
        
        # Determine hemisphere
        if lat >= 0:
            # Northern hemisphere
            utm_srid = 32600 + utm_zone
        else:
            # Southern hemisphere
            utm_srid = 32700 + utm_zone
        
        return utm_srid


class FarmGDALOperations:
    """GDAL operations specific to Farm model"""
    
    @staticmethod
    def create_farm_boundary_from_fields(farm_instance) -> Optional[Polygon]:
        """Create farm boundary polygon from all field boundaries"""
        if not hasattr(farm_instance, 'fields') or not farm_instance.fields.exists():
            return None
        
        field_boundaries = [field.boundary for field in farm_instance.fields.all()]
        
        # Create union of all field boundaries
        union_geom = field_boundaries[0]
        for boundary in field_boundaries[1:]:
            union_geom = union_geom.union(boundary)
        
        return union_geom
    
    @staticmethod
    def calculate_farm_statistics(farm_instance) -> Dict:
        """Calculate comprehensive farm statistics"""
        fields = farm_instance.fields.all()
        
        if not fields:
            return {}
        
        total_area = sum(GDALFarmHelpers.calculate_accurate_area(field.boundary) for field in fields)
        
        # Crop type distribution
        crop_distribution = {}
        for field in fields:
            crop_type = field.crop_type
            field_area = GDALFarmHelpers.calculate_accurate_area(field.boundary)
            crop_distribution[crop_type] = crop_distribution.get(crop_type, 0) + field_area
        
        # Soil type distribution
        soil_distribution = {}
        for field in fields:
            soil_type = field.soil_type
            field_area = GDALFarmHelpers.calculate_accurate_area(field.boundary)
            soil_distribution[soil_type] = soil_distribution.get(soil_type, 0) + field_area
        
        return {
            'total_area_acres': total_area,
            'total_fields': len(fields),
            'crop_distribution': crop_distribution,
            'soil_distribution': soil_distribution,
            'average_field_size': total_area / len(fields) if fields else 0
        }


class FieldGDALOperations:
    """GDAL operations specific to Field model"""
    
    @staticmethod
    def validate_field_boundary(boundary: Polygon) -> Dict:
        """Validate field boundary geometry"""
        validation_results = {
            'is_valid': boundary.valid,
            'area_acres': GDALFarmHelpers.calculate_accurate_area(boundary),
            'perimeter_meters': 0,
            'centroid': None,
            'errors': []
        }
        
        if not boundary.valid:
            validation_results['errors'].append(f"Invalid geometry: {boundary.valid_reason}")
            return validation_results
        
        # Calculate perimeter
        utm_srid = GDALFarmHelpers._get_utm_srid(boundary)
        boundary_utm = boundary.clone()
        boundary_utm.transform(utm_srid)
        validation_results['perimeter_meters'] = boundary_utm.length
        
        # Get centroid
        validation_results['centroid'] = {
            'lat': boundary.centroid.y,
            'lng': boundary.centroid.x
        }
        
        # Check minimum area
        if validation_results['area_acres'] < 0.1:
            validation_results['errors'].append("Field area is very small (< 0.1 acres)")
        
        return validation_results
    
    @staticmethod
    def split_field_into_zones(field_boundary: Polygon, num_zones: int) -> List[Polygon]:
        """Split field into irrigation zones (simplified grid approach)"""
        if num_zones <= 1:
            return [field_boundary]
        
        # Get field bounds
        bounds = field_boundary.extent  # (xmin, ymin, xmax, ymax)
        
        # Calculate grid dimensions
        grid_size = math.ceil(math.sqrt(num_zones))
        
        zones = []
        x_step = (bounds[2] - bounds[0]) / grid_size
        y_step = (bounds[3] - bounds[1]) / grid_size
        
        for i in range(grid_size):
            for j in range(grid_size):
                if len(zones) >= num_zones:
                    break
                
                x1 = bounds[0] + i * x_step
                y1 = bounds[1] + j * y_step
                x2 = bounds[0] + (i + 1) * x_step
                y2 = bounds[1] + (j + 1) * y_step
                
                # Create grid cell
                grid_cell = Polygon.from_bbox((x1, y1, x2, y2))
                
                # Intersect with field boundary
                intersection = field_boundary.intersection(grid_cell)
                if intersection and hasattr(intersection, 'area') and intersection.area > 0:
                    zones.append(intersection)
        
        return zones
    
    @staticmethod
    def calculate_field_slope_aspect(field_boundary: Polygon, elevation_data: Optional[Dict] = None) -> Dict:
        """Calculate average slope and aspect for field (requires elevation data)"""
        # This is a simplified version - in practice you'd use DEM data
        result = {
            'average_slope': None,
            'dominant_aspect': None,
            'slope_category': 'unknown'
        }
        
        if elevation_data:
            # Process elevation data here
            # This would typically involve raster analysis with GDAL
            pass
        
        return result


class SensorGDALOperations:
    """GDAL operations specific to Sensor model"""
    
    @staticmethod
    def create_sensor_coverage_area(sensor_location: Point, coverage_radius: float) -> Polygon:
        """Create circular coverage area around sensor"""
        # Transform to UTM for accurate buffer
        utm_srid = GDALFarmHelpers._get_utm_srid(sensor_location)
        sensor_utm = sensor_location.clone()
        sensor_utm.transform(utm_srid)
        
        # Create buffer
        coverage_area = sensor_utm.buffer(coverage_radius)
        
        # Transform back to WGS84
        coverage_area.transform(4326)
        
        return coverage_area
    
    @staticmethod
    def find_sensors_in_area(sensors_queryset, area: Polygon) -> List:
        """Find all sensors within a given area"""
        return [sensor for sensor in sensors_queryset if area.contains(sensor.location)]
    
    @staticmethod
    def calculate_sensor_coverage_overlap(sensor1, sensor2) -> Dict:
        """Calculate overlap between two sensor coverage areas"""
        coverage1 = SensorGDALOperations.create_sensor_coverage_area(
            sensor1.location, sensor1.coverage_radius
        )
        coverage2 = SensorGDALOperations.create_sensor_coverage_area(
            sensor2.location, sensor2.coverage_radius
        )
        
        intersection = coverage1.intersection(coverage2)
        
        return {
            'overlap_exists': intersection.area > 0,
            'overlap_area_sq_meters': GDALFarmHelpers.calculate_accurate_area(intersection, 'sq_meters') if intersection.area > 0 else 0,
            'overlap_percentage': (intersection.area / coverage1.union(coverage2).area) * 100 if intersection.area > 0 else 0
        }
    
    @staticmethod
    def optimize_sensor_placement(field_boundary: Polygon, coverage_radius: float, 
                                 min_sensors: int = 1) -> List[Point]:
        """Suggest optimal sensor placement for field coverage"""
        # Simplified grid-based approach
        field_area = GDALFarmHelpers.calculate_accurate_area(field_boundary, 'sq_meters')
        sensor_coverage_area = math.pi * (coverage_radius ** 2)
        
        # Calculate minimum sensors needed
        min_sensors_needed = max(min_sensors, math.ceil(field_area / sensor_coverage_area))
        
        # Generate grid points within field
        bounds = field_boundary.extent
        grid_size = math.ceil(math.sqrt(min_sensors_needed))
        
        suggested_points = []
        x_step = (bounds[2] - bounds[0]) / (grid_size + 1)
        y_step = (bounds[3] - bounds[1]) / (grid_size + 1)
        
        for i in range(1, grid_size + 1):
            for j in range(1, grid_size + 1):
                if len(suggested_points) >= min_sensors_needed:
                    break
                
                x = bounds[0] + i * x_step
                y = bounds[1] + j * y_step
                point = Point(x, y, srid=4326)
                
                if field_boundary.contains(point):
                    suggested_points.append(point)
        
        return suggested_points[:min_sensors_needed]


class IrrigationGDALOperations:
    """GDAL operations specific to IrrigationZone model"""
    
    @staticmethod
    def calculate_zone_water_needs(zone_boundary: Polygon, crop_coefficient: float = 1.0,
                                  reference_et: float = 5.0) -> Dict:
        """Calculate water requirements for irrigation zone"""
        area_hectares = GDALFarmHelpers.calculate_accurate_area(zone_boundary, 'hectares')
        
        # Basic water requirement calculation (simplified)
        daily_water_need_mm = reference_et * crop_coefficient
        daily_water_need_liters = daily_water_need_mm * area_hectares * 10000 / 1000
        
        return {
            'area_hectares': area_hectares,
            'daily_water_need_mm': daily_water_need_mm,
            'daily_water_need_liters': daily_water_need_liters,
            'weekly_water_need_liters': daily_water_need_liters * 7
        }
    
    @staticmethod
    def check_zone_coverage_by_sensors(zone_boundary: Polygon, sensors_list: List) -> Dict:
        """Check how well an irrigation zone is covered by sensors"""
        total_zone_area = GDALFarmHelpers.calculate_accurate_area(zone_boundary, 'sq_meters')
        covered_area = 0
        
        covering_sensors = []
        
        for sensor in sensors_list:
            sensor_coverage = SensorGDALOperations.create_sensor_coverage_area(
                sensor.location, sensor.coverage_radius
            )
            
            intersection = zone_boundary.intersection(sensor_coverage)
            if intersection.area > 0:
                covering_sensors.append(sensor)
                covered_area += GDALFarmHelpers.calculate_accurate_area(intersection, 'sq_meters')
        
        coverage_percentage = (covered_area / total_zone_area) * 100 if total_zone_area > 0 else 0
        
        return {
            'total_area_sq_meters': total_zone_area,
            'covered_area_sq_meters': covered_area,
            'coverage_percentage': min(coverage_percentage, 100),  # Cap at 100% due to overlaps
            'covering_sensors': covering_sensors,
            'num_sensors': len(covering_sensors)
        }


class WeatherStationGDALOperations:
    """GDAL operations specific to WeatherStation model"""
    
    @staticmethod
    def find_nearest_weather_station(location: Point, weather_stations_queryset) -> Optional[Dict]:
        """Find the nearest weather station to a given location"""
        if not weather_stations_queryset.exists():
            return None
        
        nearest_station = None
        min_distance = float('inf')
        
        for station in weather_stations_queryset:
            distance = GDALFarmHelpers.calculate_distance(location, station.location)
            if distance < min_distance:
                min_distance = distance
                nearest_station = station
        
        return {
            'station': nearest_station,
            'distance_meters': min_distance,
            'distance_km': min_distance / 1000
        }
    
    @staticmethod
    def calculate_weather_station_coverage(station_location: Point, 
                                         effective_range: float = 5000) -> Polygon:
        """Calculate effective coverage area for weather station"""
        return SensorGDALOperations.create_sensor_coverage_area(station_location, effective_range)


# Usage Examples and Integration Functions

class FarmSpatialAnalysis:
    """High-level spatial analysis functions combining multiple models"""
    
    @staticmethod
    def comprehensive_farm_analysis(farm_instance) -> Dict:
        """Perform comprehensive spatial analysis of entire farm"""
        analysis = {
            'farm_stats': FarmGDALOperations.calculate_farm_statistics(farm_instance),
            'fields_analysis': [],
            'sensor_coverage': {},
            'irrigation_efficiency': {},
            'weather_coverage': {}
        }
        
        # Analyze each field
        for field in farm_instance.fields.all():
            field_analysis = {
                'field_name': field.name,
                'validation': FieldGDALOperations.validate_field_boundary(field.boundary),
                'sensors': [],
                'irrigation_zones': []
            }
            
            # Analyze sensors in field
            for sensor in field.sensors.all():
                sensor_coverage = SensorGDALOperations.create_sensor_coverage_area(
                    sensor.location, sensor.coverage_radius
                )
                field_analysis['sensors'].append({
                    'sensor_name': sensor.name,
                    'coverage_area_acres': GDALFarmHelpers.calculate_accurate_area(sensor_coverage)
                })
            
            # Analyze irrigation zones
            for zone in field.irrigation_zones.all():
                zone_analysis = IrrigationGDALOperations.calculate_zone_water_needs(zone.boundary)
                zone_coverage = IrrigationGDALOperations.check_zone_coverage_by_sensors(
                    zone.boundary, field.sensors.all()
                )
                
                field_analysis['irrigation_zones'].append({
                    'zone_name': zone.name,
                    'water_needs': zone_analysis,
                    'sensor_coverage': zone_coverage
                })
            
            analysis['fields_analysis'].append(field_analysis)
        
        return analysis
    
    @staticmethod
    def export_farm_to_geojson(farm_instance) -> Dict:
        """Export farm data to GeoJSON format"""
        features = []
        
        # Add fields
        for field in farm_instance.fields.all():
            features.append({
                'type': 'Feature',
                'properties': {
                    'type': 'field',
                    'name': field.name,
                    'crop_type': field.crop_type,
                    'soil_type': field.soil_type,
                    'area_acres': GDALFarmHelpers.calculate_accurate_area(field.boundary)
                },
                'geometry': json.loads(field.boundary.geojson)
            })
        
        # Add sensors
        for field in farm_instance.fields.all():
            for sensor in field.sensors.all():
                features.append({
                    'type': 'Feature',
                    'properties': {
                        'type': 'sensor',
                        'name': sensor.name,
                        'sensor_type': sensor.sensor_type,
                        'status': sensor.status,
                        'coverage_radius': sensor.coverage_radius
                    },
                    'geometry': json.loads(sensor.location.geojson)
                })
        
        # Add weather stations
        for station in farm_instance.weather_stations.all():
            features.append({
                'type': 'Feature',
                'properties': {
                    'type': 'weather_station',
                    'name': station.name
                },
                'geometry': json.loads(station.location.geojson)
            })
        
        return {
            'type': 'FeatureCollection',
            'features': features
        }