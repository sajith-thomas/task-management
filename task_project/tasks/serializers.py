from rest_framework import serializers
from .models import Task

class TaskSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'user', 'username',
            'due_date', 'status', 'completion_report', 
            'worked_hours', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TaskCompleteSerializer(serializers.ModelSerializer):
    """Serializer for completing tasks with report and hours"""
    class Meta:
        model = Task
        fields = ['status', 'completion_report', 'worked_hours']
    
    def validate(self, data):
        """Validate that completion requires report and hours"""
        if data.get('status') == 'completed':
            if not data.get('completion_report'):
                raise serializers.ValidationError({
                    'completion_report': 'Completion report is required when marking task as completed'
                })
            if not data.get('worked_hours'):
                raise serializers.ValidationError({
                    'worked_hours': 'Worked hours is required when marking task as completed'
                })
        return data


class TaskCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new tasks"""
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'user', 'due_date', 
            'status', 'completion_report', 'worked_hours'
        ]
    
    def validate(self, data):
        """Additional validation"""
        # If status is completed, require report and hours
        if data.get('status') == 'completed':
            if not data.get('completion_report'):
                raise serializers.ValidationError({
                    'completion_report': 'Completion report is required for completed tasks'
                })
            if not data.get('worked_hours'):
                raise serializers.ValidationError({
                    'worked_hours': 'Worked hours is required for completed tasks'
                })
        return data