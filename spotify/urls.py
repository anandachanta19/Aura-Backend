from django.urls import path
from .views import detect_emotion, get_dominant_emotion, get_track_data, get_user_playlist, go_to_detect_emotion, go_to_playlist, go_to_select_emotion, hello_message, spotify_login, spotify_callback, user_profile, go_to_home, go_to_profile, go_to_library, user_library, go_to_about, get_related_tracks_view, go_to_mediaplayer, spotify_logout, get_lyrics, go_to_recommend_songs, recommend_songs, create_playlist

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
    path('spotify/playlist/', get_user_playlist, name='get_user_playlist'),
    path('spotify/track/', get_track_data, name='get_track_data'),
    path('spotify/related-tracks/', get_related_tracks_view, name='get_related_tracks'),
    path('go/mediaplayer/', go_to_mediaplayer, name='go_to_mediaplayer'),
    path('spotify/logout/', spotify_logout, name='spotify_logout'),
    path('go/select/emotion/', go_to_select_emotion, name='go_to_select_emotion'),
    path('go/detect/emotion/', go_to_detect_emotion, name='go_to_detect_emotion'),
    path('detect/emotion/', detect_emotion, name='detect_emotion'),
    path('get/dominant/emotion/', get_dominant_emotion, name='get_dominant_emotion'),
    path('spotify/lyrics/', get_lyrics, name='get_lyrics'),
    path('go/recommend/songs/', go_to_recommend_songs, name='go_to_recommend_songs'),
    path('recommend/songs/', recommend_songs, name='recommend_songs'),
    path('spotify/create-playlist/', create_playlist, name='create_playlist'),
]
