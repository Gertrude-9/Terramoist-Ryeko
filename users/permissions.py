# permissions.py
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

def role_required(allowed_roles):
    """
    Decorator to check if user has required role
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied("Authentication required")
            
            if request.user.role not in allowed_roles:
                raise PermissionDenied("Insufficient permissions")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
