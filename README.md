TerraMoist - Agricultural Monitoring System
Overview
TerraMoist is a comprehensive agricultural monitoring platform that combines sensor data, weather information, and user management to help farmers optimize crop production. The system provides real-time monitoring of soil conditions and weather patterns.

Features
Core Functionality
🌱 Soil Monitoring: Real-time soil moisture and temperature tracking
🌦️ Weather Integration: Local weather forecasts and historical data
📊 Data Visualization: Interactive charts and dashboards
🔔 Alerts & Notifications: Threshold-based alerts for critical conditions
👥 User Management: Multi-role system for farmers, agronomists, and technicians

## 🛠️ Technologies Used

- Django (Python)
Technical Components
Backend: Django REST Framework and python
Frontend: Django (planned)
Database: PostgreSQL *(Am yet to implement it currently was still usinng a default one )
API Documentation: Rest API for receiving sensor data

## 🧰 Installation Guide

1. **Clone the repository:**

Setup Instructions
git clone https://github.com/Gertrude-9/Terramoist-Ryeko.git
cd ryeko_terramoist

Installation
Python 3.8+
PostgreSQL 12+ not yet integrated into the project

2. Set up virtual environment:
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate    # Windows

3. Install dependencies:
pip install -r requirements.txt

4. Run migrations:
python manage.py migrate

5. Create superuser:
Currently am using Trudie as username and gertNaka9 as password.

Running the Application
Development Server
python manage.py runserver 8080
 http://127.0.0.1:8080/users as the landing page and then tap login and use credentials to login to the dashboard.


Project Structure
├── ryeko_terramoist/  This is the project name
├── advisory/                # Core application logic
├── sensors/                 # Sensor data processing
├── weather_data/            # Weather data integration
├── users/                   # Custom user management
├── farm/ 
├──crop
├──data_collection
├──irrigation
├──maintenance_request
├──notification
├──prediction
├──sensor_reading
├──venv          
├── manage.py
├──db.sqlite3
├──README.md
└── requirements.txt 

# Setup Instructions - README.md
# Farm Fields Monitoring System

A Django-based web application for monitoring farm fields with IoT sensors. Track humidity, temperature, and soil moisture levels with real-time alerts.

## Features

- **Field Management**: Organize farms and fields
- **Sensor Monitoring**: Track humidity, temperature, and soil moisture
- **Real-time Alerts**: Automatic threshold-based alerts
- **Interactive Dashboard**: Visual field maps and sensor data
- **Data Visualization**: Charts and graphs for sensor readings
- **Alert Management**: Resolve and track alerts

## Quick Setup

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Database Setup**
```bash
python manage.py makemigrations
python manage.py migrate
```

3. **Load Initial Data**
```bash
python manage.py loaddata fixtures/initial_data.json
```

4. **Create Superuser**
```bash
python manage.py createsuperuser
```

5. **Run Development Server**
```bash
python manage.py runserver
```

## Sample Data Setup

1. **Create sample farms and fields through Django admin**
2. **Add sensors with thresholds**:
   - Humidity: 30-80%
   - Temperature: 15-30°C
   - Soil Moisture: 40-70%

3. **Generate test readings**:
```bash
python manage.py simulate_readings --count=50
```

## API Endpoints

- `GET /api/sensor/<uuid>/readings/`: Get sensor readings
- `POST /api/add-reading/`: Add new sensor reading

## Usage Examples

### Adding Sensor Reading via API
```python
import requests
import json

data = {
    'sensor_id': 'your-sensor-uuid',
    'value': 45.5
}

response = requests.post(
    'http://localhost:8000/api/add-reading/',
    data=json.dumps(data),
    headers={'Content-Type': 'application/json'}
)
```

### Setting Up Alerts
1. Go to Django admin
2. Edit sensors to set min/max thresholds
3. Alerts will be automatically created when readings exceed thresholds

## Project Structure
```
fields/
├── models.py          # Database models
├── views.py           # View functions
├── urls.py            # URL routing
├── admin.py           # Admin interface
├── apps.py            # App configuration
├── management/
│   └── commands/
│       └── simulate_readings.py
└── templates/
    └── fields/
        ├── base.html
        ├── dashboard.html
        ├── field_detail.html
        └── alerts.html
```

## Customization

### Adding New Sensor Types
1. Update `SensorType.SENSOR_TYPES` in models.py
2. Add new sensor type via admin or fixtures
3. Update templates for new sensor icons/colors

### Extending Alert Logic
- Modify `SensorReading.check_threshold_alerts()` method
- Add custom alert conditions
- Implement notification systems (email, SMS, etc.)

## Production Deployment

1. **Security Settings**:
   - Set `DEBUG = False`
   - Configure `ALLOWED_HOSTS`
   - Use environment variables for secrets

2. **Database**:
   - Use PostgreSQL or MySQL for production
   - Configure proper database settings

3. **Static Files**:
   - Configure `STATIC_ROOT` and `STATIC_URL`
   - Use CDN for static assets

4. **Monitoring**:
   - Set up logging
   - Configure error tracking
   - Monitor sensor data ingestion

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request

## License

MIT License - feel free to use in your projects.



