from django.contrib.sessions.middleware import SessionMiddleware

class MultiSessionMiddleware(SessionMiddleware):
    def process_request(self, request):
        super().process_request(request)
        # Allow multiple sessions per user
        if not request.session.session_key:
            request.session.create()
