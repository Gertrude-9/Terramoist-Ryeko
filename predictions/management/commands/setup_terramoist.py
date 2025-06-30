# management/commands/setup_terramoist.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from predictions.models import PlantProfile, SoilSensor, UserPreferences
import json

class Command(BaseCommand):
    help = 'Setup Terramoist with initial data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--create-plants',
            action='store_true',
            help='Create default plant profiles',
        )
        parser.add_argument(
            '--create-demo-user',
            action='store_true',
            help='Create demo user with sample data',
        )
    
    def handle(self, *args, **options):
        if options['create_plants']:
            self.create_plant_profiles()
        
        if options['create_demo_user']:
            self.create_demo_user()
        
        self.stdout.write(
            self.style.SUCCESS('Terramoist setup completed successfully!')
        )
    
    def create_plant_profiles(self):
        """Create default plant profiles"""
        self.stdout.write('Creating plant profiles...')
        
        plant_data = [
            {
                'name': 'Tomato',
                'category': 'vegetable',
                'optimal_moisture_min': 60,
                'optimal_moisture_max': 80,
                'critical_low_moisture': 40,
                'critical_high_moisture': 90,
                'watering_frequency_days': 2,
                'growth_season_start': 4,
                'growth_season_end': 10,
                'description': 'Popular vegetable requiring consistent moisture'
            },
            {
                'name': 'Lettuce',
                'category': 'vegetable',
                'optimal_moisture_min': 70,
                'optimal_moisture_max': 85,
                'critical_low_moisture': 50,
                'critical_high_moisture': 95,
                'watering_frequency_days': 1,
                'growth_season_start': 3,
                'growth_season_end': 11,
                'description': 'Leafy green requiring high moisture levels'
            },
            {
                'name': 'Basil',
                'category': 'herb',
                'optimal_moisture_min': 65,
                'optimal_moisture_max': 75,
                'critical_low_moisture': 45,
                'critical_high_moisture': 85,
                'watering_frequency_days': 2,
                'growth_season_start': 5,
                'growth_season_end': 9,
                'description': 'Aromatic herb preferring well-drained moist soil'
            },
            {
                'name': 'Rose',
                'category': 'flower',
                'optimal_moisture_min': 55,
                'optimal_moisture_max': 75,
                'critical_low_moisture': 35,
                'critical_high_moisture': 85,
                'watering_frequency_days': 3,
                'growth_season_start': 4,
                'growth_season_end': 10,
                'description': 'Classic flowering plant with moderate water needs'
            },
            {
                'name': 'Succulent Mix',
                'category': 'succulent',
                'optimal_moisture_min': 20,
                'optimal_moisture_max': 40,
                'critical_low_moisture': 10,
                'critical_high_moisture': 60,
                'watering_frequency_days': 7,
                'growth_season_start': 1,
                'growth_season_end': 12,
                'description': 'Drought-resistant plants requiring minimal water'
            },
            {
                'name': 'Fern',
                'category': 'houseplant',
                'optimal_moisture_min': 75,
                'optimal_moisture_max': 90,
                'critical_low_moisture': 60,
                'critical_high_moisture': 95,
                'watering_frequency_days': 2,
                'growth_season_start': 1,
                'growth_season_end': 12,
                'description': 'Tropical plant requiring high humidity and moisture'
            }
        ]
        
        with transaction.atomic():
            for plant_info in plant_data:
                plant, created = PlantProfile.objects.get_or_create(
                    name=plant_info['name'],
                    defaults=plant_info
                )
                if created:
                    self.stdout.write(f'✓ Created plant profile: {plant.name}')
                else:
                    self.stdout.write(f'- Plant profile already exists: {plant.name}')
    
    def create_demo_user(self):
        """Create demo user with sample data"""
        self.stdout.write('Creating demo user...')
        
        # Create demo user
        demo_username = 'demo_user'
        demo_email = 'demo@terramoist.com'
        demo_password = 'demo123'
        
        with transaction.atomic():
            # Create or get demo user
            user, created = User.objects.get_or_create(
                username=demo_username,
                defaults={
                    'email': demo_email,
                    'first_name': 'Demo',
                    'last_name': 'User',
                    'is_active': True
                }
            )
            
            if created:
                user.set_password(demo_password)
                user.save()
                self.stdout.write(f'✓ Created demo user: {demo_username}')
            else:
                self.stdout.write(f'- Demo user already exists: {demo_username}')
            
            # Create user preferences
            prefs, created = UserPreferences.objects.get_or_create(
                user=user,
                defaults={
                    'notification_email': True,
                    'notification_sms': False,
                    'alert_frequency': 'immediate',
                    'timezone': 'UTC',
                    'temperature_unit': 'celsius',
                    'moisture_unit': 'percentage'
                }
            )
            
            if created:
                self.stdout.write('✓ Created user preferences')
            else:
                self.stdout.write('- User preferences already exist')
            
            # Create sample soil sensors
            sensor_data = [
                {
                    'name': 'Garden Bed 1',
                    'location': 'Front yard vegetable garden',
                    'sensor_id': 'TM001',
                    'is_active': True,
                    'plant_type': 'Tomato'
                },
                {
                    'name': 'Herb Garden',
                    'location': 'Kitchen window sill',
                    'sensor_id': 'TM002',
                    'is_active': True,
                    'plant_type': 'Basil'
                },
                {
                    'name': 'Indoor Plants',
                    'location': 'Living room',
                    'sensor_id': 'TM003',
                    'is_active': True,
                    'plant_type': 'Fern'
                }
            ]
            
            for sensor_info in sensor_data:
                # Get the plant profile
                try:
                    plant_profile = PlantProfile.objects.get(name=sensor_info['plant_type'])
                except PlantProfile.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'Plant profile {sensor_info["plant_type"]} not found, skipping sensor')
                    )
                    continue
                
                sensor, created = SoilSensor.objects.get_or_create(
                    user=user,
                    sensor_id=sensor_info['sensor_id'],
                    defaults={
                        'name': sensor_info['name'],
                        'location': sensor_info['location'],
                        'is_active': sensor_info['is_active'],
                        'plant_profile': plant_profile
                    }
                )
                
                if created:
                    self.stdout.write(f'✓ Created sensor: {sensor.name}')
                else:
                    self.stdout.write(f'- Sensor already exists: {sensor.name}')
            
            self.stdout.write(
                self.style.SUCCESS(f'Demo user setup complete. Login with: {demo_username}/{demo_password}')
            )