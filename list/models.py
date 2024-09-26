from django.db import models
from django.contrib.auth.models import User

# General task model
class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=50, choices=[('Pending', 'Pending'), ('Completed', 'Completed')], default='Pending')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')

    def __str__(self):
        return self.title

class TaskMember(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='assigned_members')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=50, choices=[('Pending', 'Pending'), ('Completed', 'Completed')], default='Pending')

    def __str__(self):
        return f"{self.user.username} - {self.task.title}"

class activitylog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)