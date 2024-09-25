import logging

logger = logging.getLogger(__name__)

class TaskLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/tasks/'):
            logger.info(f"{request.method} request by {request.user} to {request.path}")
        response = self.get_response(request)
        return response
