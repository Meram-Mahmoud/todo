from rest_framework.authtoken.views import obtain_auth_token
from .views import RegisterView
from django.urls import path
from .views import TaskListCreateView, TaskDetailView, TaskMemberUpdateView

urlpatterns = [
      path('register/', RegisterView.as_view(), name='register'),
    path('login/', obtain_auth_token, name='login'),
    # List tasks for the current user (creator or assigned)
    path('tasks/', TaskListCreateView.as_view(), name='task-list'),

    # Admin can update the task for all users
    path('tasks/<int:pk>/update/', TaskDetailView.as_view(), name='task-update'),

    # Regular users can update their own assigned task status
    path('tasks/<int:pk>/member-update/', TaskMemberUpdateView.as_view(), name='task-member-update'),
]


