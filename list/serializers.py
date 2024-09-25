from rest_framework import serializers
from .models import Task, TaskMember

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'status', 'created_by']

class TaskMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskMember
        fields = ['id', 'task', 'user', 'status']
