from django.db import models
from django.contrib.auth.models import User

class SpotifyToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    session_key = models.CharField(max_length=40)  # Store Django session key
    access_token = models.CharField(max_length=255)
    refresh_token = models.CharField(max_length=255)
    expires_at = models.DateTimeField()
    token_type = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
