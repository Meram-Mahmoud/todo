from rest_framework.permissions import BasePermission
from rest_framework import permissions

# class IsAdminOrTaskCreatorOrReadOnly(BasePermission):
#     def has_object_permission(self, request, view, obj):
#         # Admins and task creators can update the task status for all users
#         if request.user.is_staff or obj.created_by == request.user:
#             return True
#         # Regular users can only update their own task status
#         return request.method in ['GET', 'HEAD', 'OPTIONS']

class IsTaskOwnerOrAssignedOrReadOnly(BasePermission):
   

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            return obj.created_by == request.user or (obj.assigned_to == request.user and request.method == 'PATCH')
        
        return False
    
class AllowAny(permissions.BasePermission):
    """
    Custom permission to allow any user to access the view.
    """
    def has_permission(self, request, view):
        return True