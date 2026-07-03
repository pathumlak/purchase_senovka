from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def superadmin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            if request.user.is_authenticated and request.user.profile.is_superadmin():
                return view_func(request, *args, **kwargs)
        except Exception:
            pass
        messages.error(request, 'Access denied. Super Admin privileges required.')
        return redirect('home')
    return wrapper
