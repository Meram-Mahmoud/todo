from django.shortcuts import render
from fcm_django.models import FCMDevice
from django.conf import settings
# Create your views here.
from rest_framework.permissions import IsAuthenticated
from .models import Task, TaskMember
from .serializers import TaskSerializer, TaskMemberSerializer
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework import generics, status
from rest_framework.response import Response
from .models import Task, TaskMember
from .serializers import TaskSerializer, TaskMemberSerializer
from .permissions import IsTaskOwnerOrAssignedOrReadOnly
from rest_framework.permissions import AllowAny


class RegisterView(APIView):
    permission_classes = [AllowAny]  # Allow any user to register

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        if username and password:
            user = User.objects.create_user(username=username, password=password)
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "message": "User created successfully",
                "token": token.key
            }, status=status.HTTP_201_CREATED)
        return Response({"error": "Missing credentials"}, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)


class TaskListCreateView(generics.ListCreateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]


    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        return Task.objects.filter(created_by=self.request.user) | Task.objects.filter(task_members__user=self.request.user)

class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsTaskOwnerOrAssignedOrReadOnly]

    def perform_update(self, serializer):
        task = serializer.save()
        assigned_users = task.task_members.values_list('user', flat=True)
        send_task_update_notification(task, assigned_users)


class TaskMemberUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TaskMemberSerializer

    def get_queryset(self):
        # Only allow the user to update their own assigned tasks
        return TaskMember.objects.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        task_member = self.get_object()

        # Update the status only for the individual user, not the entire task
        task_member.status = request.data.get('status', task_member.status)
        task_member.save()

        return Response({'message': 'Task status updated for the user.'}, status=status.HTTP_200_OK)
    
def send_task_update_notification(task, users):
    devices = FCMDevice.objects.filter(user__in=users)
    devices.send_message(
        title="Task Update",
        body=f"Task '{task.title}' has been updated.",
    )


   






