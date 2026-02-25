from django.shortcuts import redirect
from django.contrib import messages

def superadmin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.profile.role == 'superadmin':
                return view_func(request, *args, **kwargs)
        messages.error(request, "Access Denied. SuperAdmin only.")
        return redirect('login')
    return wrapper