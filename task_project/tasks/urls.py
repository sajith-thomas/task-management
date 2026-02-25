from django.urls import path
from .views import UserTasksView, UpdateTaskStatus, TaskReportView
from . import views

urlpatterns = [
    path('add/', views.add_task, name='add_task'),
    path('delete/<int:id>/', views.delete_task, name='delete_task'),
    path('tasks/', UserTasksView.as_view(), name='user_tasks'),
    path('tasks/<int:id>/', UpdateTaskStatus.as_view(), name='update_task'),
    path('tasks/<int:id>/report/', TaskReportView.as_view(), name='task_report'),
    
    path('superadmin/dashboard/', views.superadmin_dashboard, name='superadmin_dashboard'),
    path('add-task/', views.add_task, name='add_task'),
    path('update-task/<int:id>/', views.update_task, name='update_task'),
    path('delete-task/<int:id>/', views.delete_task, name='delete_task'),
]