from django.conf import settings
from django.db import models
from sensors.models import Sensor

class Farm(models.Model):
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='farms'
    )
    location = models.CharField(max_length=300)
    total_fields = models.PositiveIntegerField(
        default=0,
        help_text="Number of fields in this farm"
    )
    total_area = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Total farm area in acres"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Farm'
        verbose_name_plural = 'Farms'
