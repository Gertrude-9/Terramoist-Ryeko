# tasks.py
from celery import shared_task
from django.core.management import call_command

@shared_task
def fetch_weather_data():
    call_command('fetch_weather')