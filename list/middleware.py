from .models import activitylog

from django.utils.timezone import now

class ActivityLoggingMiddleware:
   
    def __init__(self, get_response):
       
        self.get_response = get_response

    def __call__(self, request):
        """
        Code to be executed for each request before the view (and later middleware) is called.
        """
        response = self.get_response(request)

        user = request.user if request.user.is_authenticated else None  
        method = request.method
        path = request.path

        activitylog.objects.create(
            user=user,
            method=method,
            path=path,
            timestamp=now()
        )

        return response
