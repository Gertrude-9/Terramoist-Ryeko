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



