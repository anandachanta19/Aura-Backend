from django.urls import path
from .views import *

urlpatterns = [
    path('hello/', hello_message, name='frontend_connection'),
    path('spotify/login/', spotify_login, name='spotify_auth'),
    path('spotify/callback/', spotify_callback, name='spotify_callback'),
    path('user/profile/', user_profile, name='user_profile'),
    path('go/home', go_to_home, name='go_to_home'),
    path('go/profile', go_to_profile, name='go_to_profile')
]
