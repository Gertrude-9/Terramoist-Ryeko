from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser with agricultural-specific fields
    """
    
    class Role(models.TextChoices):
        FARMER = 'farmer', _('Farmer')
        AGRONOMIST = 'agronomist', _('Agronomist')
        TECHNICIAN = 'technician', _('Technician')
        ADMIN = 'admin', _('System Administrator')
    
    # User Information
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.FARMER,
        verbose_name=_('User Role'),
        help_text=_("The role determines the user's permissions and access level")
    )
    
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name=_('Phone Number'),
        help_text=_("User's primary contact number")
    )
    
    address = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Physical Address'),
        help_text=_("User's physical location address")
    )
    
    # Agricultural Specific Fields
    farm_size = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_('Farm Size'),
        help_text=_("Farm size in acres (for farmers only)")
    )

    USER_ROLES = [
        ('farmer', 'Farmer'),
        ('agronomist', 'Agronomist'),
        ('technician', 'Technician'),
        ('admin', 'System Administrator'),
    ]

    
    specialization = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Specialization'),
        help_text=_("Area of expertise (for agronomists/technicians)")
    )
    
    # Status Fields
    is_verified = models.BooleanField(
        default=False,
        verbose_name=_('Verified Status'),
        help_text=_("Designates whether the user has been verified by the system")
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
    
    @property
    def is_farmer(self):
        return self.role == self.Role.FARMER
    
    @property
    def is_agronomist(self):
        return self.role == self.Role.AGRONOMIST
    
    @property
    def is_technician(self):
        return self.role == self.Role.TECHNICIAN
    
    @property
    def is_system_admin(self):
        return self.role == self.Role.ADMIN