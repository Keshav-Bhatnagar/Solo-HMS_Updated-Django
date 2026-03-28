from django.db import DatabaseError
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)

class DatabaseHealthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            from django.db import connections
            conn = connections['default']
            if not conn.is_usable():
                conn.close()
                conn.connect()
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
        except DatabaseError as e:
            logger.critical(f"Database connection failure: {str(e)}")
            return JsonResponse({
                'error': 'System temporarily unavailable',
                'status': 'database_error'
            }, status=503)
            
        return self.get_response(request)