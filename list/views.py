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

from django.contrib.auth import authenticate
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView


from django.contrib.auth.models import User
from .models import Task, TaskMember

from .serializers import TaskSerializer, TaskMemberSerializer





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
    
@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
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
    

@api_view(['POST'])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    user = authenticate(username=username, password=password)
    
    if user:
        if user.check_password(password):
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "message": "Login successful",
                "token": token.key
            }, status=status.HTTP_200_OK)
        return Response({"error": "Incorrect password"}, status=status.HTTP_401_UNAUTHORIZED)
    
    return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)



class TaskListCreateView(generics.ListCreateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]


    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        return Task.objects.filter(created_by=self.request.user) | Task.objects.filter(task_members__user=self.request.user)
    
from django.db.models import Q

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def task_list_create_view(request):
    if request.method == 'GET':
        tasks = Task.objects.filter(
            Q(created_by=request.user) | Q(task_members__user=request.user)
        ).distinct()
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
    
@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def task_detail_view(request, pk):
    try:
        task = Task.objects.get(pk=pk)
    except Task.DoesNotExist:
        return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

    # GET - Retrieve task information for admin and assigned members
    if request.method == 'GET':
        if request.user == task.created_by or task.task_members.filter(user=request.user).exists():
            serializer = TaskSerializer(task)
            return Response(serializer.data)
        return Response({"error": "Not authorized to view this task"}, status=status.HTTP_403_FORBIDDEN)
    
    # POST - Admin can update task, assign users, and change task status
    elif request.method == 'POST':
        if request.user == task.created_by:  # Admin logic
            serializer = TaskSerializer(task, data=request.data, partial=True)
            if serializer.is_valid():
                updated_task = serializer.save()

                # Assign users to the task
                assigned_users = request.data.get('assigned_users')
                if assigned_users:
                    for user_id in assigned_users:
                        user = User.objects.get(id=user_id)
                        TaskMember.objects.get_or_create(task=updated_task, user=user)

                # Update task status for all members
                if 'status' in request.data:
                    TaskMember.objects.filter(task=updated_task).update(status=request.data['status'])

                # Notify assigned users about task update
                assigned_user_ids = updated_task.task_members.values_list('user', flat=True)
                send_task_update_notification(updated_task, assigned_user_ids)

                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        elif task.task_members.filter(user=request.user).exists():  # Member logic
            task_member = TaskMember.objects.get(task=task, user=request.user)
            task_member.status = request.data.get('status', task_member.status)
            task_member.save()
            return Response({'message': 'Task status updated for the member.'}, status=status.HTTP_200_OK)
        
        return Response({"error": "Not authorized to update this task"}, status=status.HTTP_403_FORBIDDEN)

    # DELETE - Only task creator can delete the task
    elif request.method == 'DELETE':
        if request.user == task.created_by:
            assigned_users = task.task_members.values_list('user', flat=True)
            
            # Notify users of task deletion
            send_task_deletion_notification(task, assigned_users)
            
            task.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        return Response({"error": "Only the task creator can delete this task"}, status=status.HTTP_403_FORBIDDEN)


    
def send_task_update_notification(task, users):
    devices = FCMDevice.objects.filter(user__in=users)
    devices.send_message(
        title="Task Update",
        body=f"Task '{task.title}' has been updated.",
    )



from fcm_django.models import FCMDevice

def send_task_update_notification(task, users):
 
    devices = FCMDevice.objects.filter(user__in=users)
    if devices.exists():
        devices.send_message(
            title="Task Update",
            body=f"Task '{task.title}' has been updated."
        )
    else:
        print("No devices registered for these users.")


def send_task_deletion_notification(task, users):

    devices = FCMDevice.objects.filter(user__in=users)
    if devices.exists():
        devices.send_message(
            title="Task Deletion",
            body=f"Task '{task.title}' has been deleted."
        )
    else:
        print("No devices registered for these users.")


