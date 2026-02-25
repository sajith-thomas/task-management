from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Task
from .serializers import TaskSerializer, TaskCompleteSerializer, TaskCreateSerializer
from accounts.decorators import superadmin_required

# ============= USER API VIEWS (Session Auth) =============

class UserTasksView(APIView):
    """GET /api/user/tasks/ - Get tasks for logged-in user"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tasks = Task.objects.filter(user=request.user)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)


class UpdateTaskStatus(APIView):
    """PUT /api/user/tasks/<id>/ - Update task status"""
    permission_classes = [IsAuthenticated]

    def put(self, request, id):
        task = get_object_or_404(Task, id=id, user=request.user)
        serializer = TaskCompleteSerializer(task, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Task updated successfully", "task": serializer.data})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============= ADMIN API VIEWS =============

class TaskReportView(APIView):
    """GET /api/admin/tasks/<id>/report/ - Get task report (admin only)"""
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        profile = request.user.profile

        if profile.role not in ['admin', 'superadmin']:
            return Response({"error": "Not allowed"}, status=status.HTTP_403_FORBIDDEN)

        task = get_object_or_404(Task, id=id, status='completed')
        serializer = TaskSerializer(task)
        return Response(serializer.data)


class TaskListView(APIView):
    """GET /api/admin/tasks/ - Get all tasks (admin only)"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.profile
        if profile.role not in ['admin', 'superadmin']:
            return Response({"error": "Not allowed"}, status=status.HTTP_403_FORBIDDEN)
            
        tasks = Task.objects.all()
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)


# ============= JWT API VIEWS (for regular users with token auth) =============

class IsRegularUser(permissions.BasePermission):
    """Permission class for regular users only"""
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and 
                hasattr(request.user, 'profile') and 
                request.user.profile.role == 'user')


class UserTaskListAPIView(generics.ListAPIView):
    """GET /api/tasks/ - JWT protected endpoint for regular users"""
    serializer_class = TaskSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsRegularUser]
    
    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)


class UserTaskUpdateAPIView(generics.UpdateAPIView):
    """PUT /api/tasks/<id>/ - JWT protected endpoint for updating tasks"""
    serializer_class = TaskCompleteSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsRegularUser]
    
    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Additional validation (though serializer already handles this)
        if serializer.validated_data.get('status') == 'completed':
            if not serializer.validated_data.get('completion_report'):
                return Response(
                    {'error': 'Completion report is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not serializer.validated_data.get('worked_hours'):
                return Response(
                    {'error': 'Worked hours is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        self.perform_update(serializer)
        return Response(serializer.data)


# ============= WEB VIEWS (Admin Panel) =============

@login_required
def superadmin_dashboard(request):
    """SuperAdmin dashboard view - only accessible by superadmin"""
    # Check if user is superadmin
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'superadmin':
        messages.error(request, "You don't have permission to access this page.")
        return redirect('profile')
    
    users = User.objects.all()
    tasks = Task.objects.all().select_related('user')
    
    context = {
        'users': users,
        'tasks': tasks,
    }
    return render(request, 'superadmin_dashboard.html', context)


@login_required
def delete_task(request, id):
    """Delete task view - only accessible by superadmin"""
    # Check if user is superadmin
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'superadmin':
        messages.error(request, "You don't have permission to delete tasks.")
        return redirect('profile')
    
    task = get_object_or_404(Task, id=id)
    task.delete()
    messages.success(request, "Task deleted successfully")
    return redirect("superadmin_dashboard")


@login_required
def add_task(request):
    """Add new task view - accessible by all authenticated users"""
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        due_date = request.POST.get("due_date")
        status = request.POST.get("status", "pending")
        completion_report = request.POST.get("completion_report", "")
        worked_hours = request.POST.get("worked_hours")
        
        # Convert worked_hours to float if provided
        if worked_hours:
            worked_hours = float(worked_hours)
        else:
            worked_hours = None

        # Get user_id from form or use current user
        user_id = request.POST.get("user_id")
        
        # For regular users, force assignment to themselves
        if request.user.profile.role == 'user':
            assigned_user = request.user
        else:
            # For admins and superadmins, they can assign to any user
            if user_id:
                assigned_user = User.objects.get(id=user_id)
            else:
                assigned_user = request.user

        # Create the task
        Task.objects.create(
            title=title,
            description=description,
            user=assigned_user,
            due_date=due_date,
            status=status,
            completion_report=completion_report,
            worked_hours=worked_hours
        )
        
        messages.success(request, "Task created successfully")
        
        # Redirect based on role
        if request.user.profile.role == 'superadmin':
            return redirect("superadmin_dashboard")
        else:
            return redirect("profile")

    # GET request - show form
    # Determine which users to show in dropdown based on role
    if request.user.profile.role == 'superadmin':
        users = User.objects.all()
    elif request.user.profile.role == 'admin':
        users = User.objects.filter(profile__assigned_admin=request.user) | User.objects.filter(id=request.user.id)
    else:
        # Regular users - only show themselves
        users = User.objects.filter(id=request.user.id)
    
    return render(request, "add_task.html", {
        "users": users,
        "user_role": request.user.profile.role
    })


@login_required
def update_task(request, id):
    """Update task view"""
    task = get_object_or_404(Task, id=id)
    
    # Check if user has permission to update this task
    if request.user.profile.role == 'user' and task.user != request.user:
        messages.error(request, "You can only update your own tasks.")
        return redirect('profile')
    
    if request.method == "POST":
        task.title = request.POST.get("title", task.title)
        task.description = request.POST.get("description", task.description)
        task.due_date = request.POST.get("due_date", task.due_date)
        task.status = request.POST.get("status", task.status)
        
        # Handle completion fields
        if task.status == "completed":
            task.completion_report = request.POST.get("completion_report", "")
            worked_hours = request.POST.get("worked_hours")
            if worked_hours:
                task.worked_hours = float(worked_hours)
        
        task.save()
        messages.success(request, "Task updated successfully")
        
        # Redirect based on role
        if request.user.profile.role == 'superadmin':
            return redirect("superadmin_dashboard")
        else:
            return redirect("profile")
    
    # GET request - show form
    # Determine which users to show in dropdown based on role
    if request.user.profile.role == 'superadmin':
        users = User.objects.all()
    elif request.user.profile.role == 'admin':
        users = User.objects.filter(profile__assigned_admin=request.user) | User.objects.filter(id=request.user.id)
    else:
        # Regular users - only show themselves
        users = User.objects.filter(id=request.user.id)
    
    return render(request, "update_task.html", {
        "task": task, 
        "users": users,
        "user_role": request.user.profile.role
    })