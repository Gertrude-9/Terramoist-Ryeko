from celery import shared_task
from .services import IrrigationService

@shared_task
def check_irrigation_needs():
    IrrigationService.check_irrigation_needs()
    return "Checked irrigation needs"

@shared_task
def check_scheduled_irrigation():
    IrrigationService.check_scheduled_irrigation()
    return "Checked scheduled irrigation"