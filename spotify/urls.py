from django.urls import path
from .views import get_user_playlist, go_to_playlist, hello_message, spotify_login, spotify_callback, user_profile, go_to_home, go_to_profile, go_to_library, user_library, go_to_about

urlpatterns = [
    path('hello/', hello_message, name='frontend_connection'),
    path('spotify/login/', spotify_login, name='spotify_auth'),
    path('spotify/callback/', spotify_callback, name='spotify_callback'),
    path('user/profile/', user_profile, name='user_profile'),
    path('go/home', go_to_home, name='go_to_home'),
    path('go/profile', go_to_profile, name='go_to_profile'),
    path('go/library', go_to_library, name='go_to_library'),
    path("spotify/library/", user_library, name="user-library"),
    path('go/about', go_to_about, name='go_to_about'),
    path('go/playlist/', go_to_playlist, name='go_to_playlist'),
    path('spotify/playlist/', get_user_playlist, name='get_user_playlist')
]
