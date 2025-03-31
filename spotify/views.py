import spotipy
from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.decorators import api_view
from spotify.models import SpotifyToken
from spotify.services.spotify_mediaplayer import get_track_details, get_related_tracks
from .handlers.session_handler import SpotifySessionHandler
from django.utils import timezone
from .services.spotify_utils import get_spotify_token_by_session
from .services.spotify_profile import get_user_profile, get_user_top_artists, get_user_playlists
from .services.spotify_library import get_recently_played_tracks, get_user_playlists
from .services.spotify_playlist import get_playlist_details

@api_view(['GET'])
def hello_message(request):
    return Response({"message":"Hello From Django"})

@api_view(['GET'])
def spotify_login(request):
    """Redirect user to Spotify login."""
    handler = SpotifySessionHandler(request)
    return redirect(handler.get_auth_url())

@api_view(['GET'])
def spotify_callback(request):
    """Handle Spotify OAuth callback."""
    handler = SpotifySessionHandler(request)
    try:
        if handler.handle_callback():
            # Get the access token information
            token_info = handler.auth_manager.get_access_token(request.GET['code'])

            # Fetch the Spotify user id
            sp = spotipy.Spotify(auth=token_info['access_token'])
            spotify_user = sp.current_user()
            spotify_user_id = spotify_user.get('id')

            # Fetch or create a Django user object based on Spotify user ID
            user, created = User.objects.get_or_create(username=spotify_user_id)

            # Save the token associated with this user
            SpotifyToken.objects.update_or_create(
                user=user,
                defaults={
                    'session_key': request.session.session_key,
                    'access_token': token_info['access_token'],
                    'refresh_token': token_info['refresh_token'],
                    'expires_at': timezone.now() + timezone.timedelta(seconds=token_info['expires_in']),
                    'token_type': token_info['token_type']
                }
            )

            # Redirect to frontend with session key
            session_key = request.session.session_key
            return redirect(f"http://localhost:5173/home?session={session_key}")
    except PermissionDenied as e:
        print(f"Error during callback: {e}")

    return Response({"error": "Authentication failed"}, status=400)


@api_view(['GET'])
def user_profile(request):
    """Fetch user's Spotify profile data."""
    session_key = request.GET.get('session')
    if not session_key:
        return Response({"error": "Session key is required"}, status=400)

    # Retrieve token using session key
    token = get_spotify_token_by_session(session_key)
    if not token:
        return Response({"error": "Invalid session or token not found"}, status=401)

    try:
        profile_data = get_user_profile(token)
        profile_data["top_artists"] = get_user_top_artists(token, limit=5)
        profile_data["playlists"] = get_user_playlists(token, limit=5)

        return Response(profile_data, status=200)
    except Exception as e:
        print(f"Error fetching Spotify data: {e}")
        return Response({"error": "Failed to fetch user data"}, status=500)

@api_view(['GET'])
def go_to_home(request):
    """Redirect to the home page with the session key."""
    session_key = request.GET.get("session")
    if not session_key:
        return JsonResponse({"error": "Session key is missing."}, status=400)

    return JsonResponse({"redirect_url": f"http://localhost:5173/home?session={session_key}"}, status=200)

@api_view(['GET'])
def go_to_profile(request):
    """Redirect to the profile page with the session key."""
    session_key = request.GET.get("session")
    if not session_key:
        return JsonResponse({"error": "Session key is missing."}, status=400)

    return JsonResponse({"redirect_url": f"http://localhost:5173/profile?session={session_key}"}, status=200)

@api_view(['GET'])
def go_to_library(request):
    """Redirect to the profile page with the session key."""
    session_key = request.GET.get("session")
    if not session_key:
        return JsonResponse({"error": "Session key is missing."}, status=400)

    return JsonResponse({"redirect_url": f"http://localhost:5173/library?session={session_key}"}, status=200)

@api_view(['GET'])
def go_to_about(request):
    """Redirect to the profile page with the session key."""
    session_key = request.GET.get("session")
    if not session_key:
        return JsonResponse({"error": "Session key is missing."}, status=400)

    return JsonResponse({"redirect_url": f"http://localhost:5173/about?session={session_key}"}, status=200)

@api_view(['GET'])
def user_library(request):
    """Fetch user's recently played tracks and playlists."""
    session_key = request.GET.get('session')
    if not session_key:
        return Response({"error": "Session key is required"}, status=400)

    # Retrieve token using session key
    token = get_spotify_token_by_session(session_key)
    if not token:
        return Response({"error": "Invalid session or token not found"}, status=401)

    try:
        recently_played = get_recently_played_tracks(token, limit=10)
        playlists = get_user_playlists(token, limit=10)

        return Response({
            "recently_played": recently_played,
            "playlists": playlists
        }, status=200)
    except Exception as e:
        print(f"Error fetching Spotify library data: {e}")
        return Response({"error": "Failed to fetch user data"}, status=500)
    
@api_view(['GET'])
def go_to_playlist(request):
    session_key = request.GET.get("session")
    playlist_id = request.GET.get("playlist_id")
    if not session_key:
        return JsonResponse({"error": "Session key is missing."}, status=400)

    return JsonResponse({"redirect_url": f"http://localhost:5173/playlist?session={session_key}&playlist_id={playlist_id}"}, status=200)
      
@api_view(["GET"])
def get_user_playlist(request):
    # Fetch a user's playlist details including the songs inside it.
    session_key = request.GET.get("session")
    print(session_key)
    playlist_id = request.GET.get("playlist_id")
    print(playlist_id)

    if not session_key or not playlist_id:
        return Response({"error": "Session key and playlist ID are required"}, status=400)

    token = get_spotify_token_by_session(session_key)
    if not token:
        return Response({"error": "Invalid session or token not found"}, status=401)

    try:
        playlist_data = get_playlist_details(token, playlist_id)
        for track in playlist_data.get("songs", []):
            track["accessToken"] = token.access_token  # Include access token for each track
        return Response(playlist_data, status=200)
    except Exception as e:
        print(f"Error fetching playlist data: {e}")
        return Response({"error": "Failed to fetch playlist data"}, status=500)


@api_view(["GET"])
def get_track_data(request):
    """
    API view to return track details for playback.
    Expects 'session' and 'track_id' as query parameters.
    """
    session_key = request.GET.get("session")
    track_id = request.GET.get("track_id")
    
    if not session_key or not track_id:
        return Response({"error": "Session key and track ID are required"}, status=400)
    
    token = get_spotify_token_by_session(session_key)
    if not token:
        return Response({"error": "Invalid session or token not found"}, status=401)
    
    try:
        track_data = get_track_details(token, track_id)
        # Optionally, you might include the access token (if safe to do so)
        # for the Web Playback SDK. In production, use secure methods.
        track_data["accessToken"] = token.access_token
        return Response(track_data, status=200)
    except Exception as e:
        return Response({"error": "Failed to fetch track data"}, status=500)

@api_view(["GET"])
def get_related_tracks_view(request):
    """
    API view to return related tracks for a given track ID.
    Expects 'session' and 'track_id' as query parameters.
    """
    session_key = request.GET.get("session")
    track_id = request.GET.get("track_id")

    if not session_key or not track_id:
        return Response({"error": "Session key and track ID are required"}, status=400)

    token = get_spotify_token_by_session(session_key)
    if not token:
        return Response({"error": "Invalid session or token not found"}, status=401)

    try:
        related_tracks = get_related_tracks(token, track_id)
        if not related_tracks:
            return Response({"message": "No related tracks found for the given track."}, status=404)
        return Response({"tracks": related_tracks}, status=200)  # Wrap related tracks in a "tracks" key
    except Exception as e:
        print(f"Error fetching related tracks: {e}")
        return Response({"error": "Failed to fetch related tracks"}, status=500)

@api_view(['GET'])
def go_to_mediaplayer(request):
    """
    Redirect to the media player page with session and playlist or track ID.
    """
    session_key = request.GET.get("session")
    playlist_id = request.GET.get("playlist_id")
    track_id = request.GET.get("track_id")

    if not session_key:
        return JsonResponse({"error": "Session key is required."}, status=400)

    if playlist_id:
        redirect_url = f"http://localhost:5173/mediaplayer?session={session_key}&playlist_id={playlist_id}"
    elif track_id:
        redirect_url = f"http://localhost:5173/mediaplayer?session={session_key}&track_id={track_id}"
    else:
        return JsonResponse({"error": "Either playlist ID or track ID is required."}, status=400)

    return JsonResponse({"redirect_url": redirect_url}, status=200)
