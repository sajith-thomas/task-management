from django.shortcuts import render

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from tasks.models import Task
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import Profile
from rest_framework_simplejwt.tokens import RefreshToken
import json
from django.contrib import messages



@login_required
def superadmin_dashboard(request):
    if request.user.profile.role != 'superadmin':
        return redirect('not_allowed')

    users = request.user.__class__.objects.all()
    tasks = Task.objects.all()

    return render(request, 'superadmin_dashboard.html', {
        'users': users,
        'tasks': tasks
    })


@login_required
def admin_dashboard(request):
    if request.user.profile.role != 'admin':
        return redirect('not_allowed')

    users = request.user.profile.user.users_under_admin.all()
    tasks = Task.objects.filter(assigned_to__profile__assigned_admin=request.user)

    return render(request, 'admin_dashboard.html', {
        'users': users,
        'tasks': tasks
    })

###########################


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # Redirect based on role
            if user.profile.role == 'superadmin':
                return redirect('superadmin_dashboard')
            elif user.profile.role == 'admin':
                return redirect('admin_dashboard')
            else:  # Regular user
                # Instead of showing error, redirect to JWT token page
                return redirect('user_token_page')  # We'll create this

        else:
            messages.error(request, "Invalid username or password")

    return render(request, 'login.html')


############`################

from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect

def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect('signup')

        # Create user (signal will auto-create profile)
        user = User.objects.create_user(
            username=username,
            password=password
        )

        # Update the auto-created profile
        user.profile.role = role
        user.profile.save()

        messages.success(request, "Account created successfully")
        return redirect('login')

    return render(request, 'signup.html')

###########

def logout_view(request):
    logout(request)
    return redirect('login')

#############

# accounts/views.py (add this function)
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from tasks.models import Task
from django.contrib.auth.models import User
from django.db.models import Sum

@login_required
def profile_view(request):
    user = request.user
    
    # FIX: Use 'user' instead of 'assigned_to' (based on your model)
    tasks = Task.objects.filter(user=user).order_by('-created_at')
    
    # Calculate statistics
    total_tasks = tasks.count()
    pending_tasks = tasks.filter(status='pending').count()
    in_progress_tasks = tasks.filter(status='in_progress').count()
    completed_tasks = tasks.filter(status='completed').count()
    
    # Calculate total hours worked
    total_hours = tasks.filter(
        status='completed'
    ).aggregate(Sum('worked_hours'))['worked_hours__sum'] or 0
    
    # Get completed tasks for reports
    completed_tasks_list = tasks.filter(status='completed').order_by('-updated_at')
    
    context = {
        'user': user,
        'tasks': tasks,
        'total_tasks': total_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'completed_tasks': completed_tasks,
        'total_hours': round(total_hours, 1),
        'completed_tasks_list': completed_tasks_list,
    }
    
    return render(request, 'profile.html', context)

##########

def user_token_page(request):
    """Display JWT tokens for authenticated regular users"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Check if user is regular user
    if request.user.profile.role != 'user':
        messages.error(request, "This page is only for regular users")
        if request.user.profile.role == 'superadmin':
            return redirect('superadmin_dashboard')
        elif request.user.profile.role == 'admin':
            return redirect('admin_dashboard')
    
    # Generate JWT tokens
    refresh = RefreshToken.for_user(request.user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)
    
    context = {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'username': request.user.username,
    }
    
    return render(request, 'user_token_page.html', context)

def user_logout_view(request):
    """Logout user and clear session"""
    logout(request)
    return redirect('login')