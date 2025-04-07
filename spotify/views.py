import os
import spotipy
from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.decorators import api_view
from spotify.models import SpotifyToken, ActiveSession
from spotify.services.spotify_mediaplayer import get_track_details, get_related_tracks
from .handlers.session_handler import SpotifySessionHandler
from django.utils import timezone
from .services.spotify_utils import get_spotify_token_by_session, refresh_spotify_token
from .services.spotify_profile import get_user_profile, get_user_top_artists, get_user_playlists
from .services.spotify_library import get_recently_played_tracks, get_user_playlists
from .services.spotify_playlist import get_playlist_details
import cv2
from deepface import DeepFace
import numpy as np
import base64
import json
from django.views.decorators.csrf import csrf_exempt
import requests
from transformers import pipeline
import json
import lyricsgenius
import re
import random

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

            # Create or update active session
            ActiveSession.objects.update_or_create(
                session_key=session_key,
                defaults={'is_active': True}
            )

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

@api_view(['GET'])
def spotify_logout(request):
    """Handle user logout."""
    session_key = request.GET.get("session")
    if not session_key:
        return JsonResponse({"error": "Session key is missing."}, status=400)

    try:
        # Invalidate the session
        ActiveSession.objects.filter(session_key=session_key).update(is_active=False)
        # Delete the token
        SpotifyToken.objects.filter(session_key=session_key).delete()
        # Clear session data
        request.session.flush()
        return JsonResponse({"redirect_url": "http://localhost:5173"}, status=200)
    except Exception as e:
        print(f"Error during logout: {e}")
        return JsonResponse({"error": "Failed to logout"}, status=500)

def validate_session(session_key):
    """Validate if a session is active"""
    return ActiveSession.objects.filter(
        session_key=session_key,
        is_active=True
    ).exists()

@api_view(['GET'])
def go_to_select_emotion(request):
    session_key = request.GET.get("session")
    if not session_key:
        return JsonResponse({"error": "Session key is missing."}, status=400)

    return JsonResponse({"redirect_url": f"http://localhost:5173/select/emotion?session={session_key}"}, status=200)

@api_view(['GET'])
def go_to_detect_emotion(request):
    session_key = request.GET.get("session")
    if not session_key:
        return JsonResponse({"error": "Session key is missing."}, status=400)

    return JsonResponse({"redirect_url": f"http://localhost:5173/detect/emotion?session={session_key}"}, status=200)

@csrf_exempt
def detect_emotion(request):
    """Detect emotions from an image sent via POST request."""
    session_key = request.GET.get("session") or request.POST.get("session")  # Check both GET and POST
    if not session_key or not validate_session(session_key):
        return JsonResponse({"error": "Invalid or missing session key"}, status=401)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            image_data = data['image'].split(',')[1]  # Remove "data:image/jpeg;base64,"
            decoded_image = base64.b64decode(image_data)
            np_image = np.frombuffer(decoded_image, np.uint8)
            frame = cv2.imdecode(np_image, cv2.IMREAD_COLOR)

            if frame is None or frame.size == 0:
                return JsonResponse({'error': 'Invalid image data'}, status=400)

            # Resize frame to reduce memory usage (optional)
            frame = cv2.resize(frame, (640, 480))

            # Initialize emotion count
            emotion_count = {'happy': 0, 'angry': 0, 'sad': 0, 'surprise': 0, 'neutral': 0, 'fear': 0}

            # Convert to grayscale for face detection
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Detect faces using Haar Cascade
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_alt2.xml')
            faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

            for (x, y, w, h) in faces:
                # Ensure ROI is within bounds
                x, y = max(0, x), max(0, y)
                w, h = min(w, gray_frame.shape[1] - x), min(h, gray_frame.shape[0] - y)
                if w <= 0 or h <= 0:
                    continue

                # Extract face ROI from original frame (BGR) and convert to RGB
                face_roi = frame[y:y + h, x:x + w]
                face_roi_rgb = cv2.cvtColor(face_roi, cv2.COLOR_BGR2RGB)

                # Analyze emotions with DeepFace
                try:
                    result = DeepFace.analyze(face_roi_rgb, actions=['emotion'], enforce_detection=False)
                    emotion = result[0]['dominant_emotion']
                    if emotion in emotion_count:
                        emotion_count[emotion] += 1
                except Exception as e:
                    print(f"Error analyzing emotion: {e}")
                    continue

            return JsonResponse(emotion_count)

        except Exception as e:
            print(f"Error in detect_emotion: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def get_dominant_emotion(request):
    """Determine the dominant emotion from cumulative emotion counts."""
    session_key = request.GET.get("session") or request.POST.get("session")
    if not session_key or not validate_session(session_key):
        return JsonResponse({"error": "Invalid or missing session key"}, status=401)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            emotion_count = data['emotion_count']
            if not emotion_count:
                return JsonResponse({'error': 'No emotion_count provided'}, status=400)

            dominant_emotion = max(emotion_count, key=emotion_count.get)
            return JsonResponse({'dominant_emotion': dominant_emotion})

        except Exception as e:
            print(f"Error in get_dominant_emotion: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@api_view(['GET'])
def get_lyrics(request):
    """
    Fetch lyrics for a given song using Genius API.
    Removes everything before the word 'Lyrics' and returns lyrics from the first verse.
    Expects 'session', 'song_title', and 'artist_name' as query parameters.
    """
    session_key = request.GET.get("session")
    song_title = request.GET.get("song_title")
    artist_name = request.GET.get("artist_name")

    if not session_key or not song_title or not artist_name:
        return JsonResponse({"error": "Session key, song title, and artist name are required."}, status=400)

    # Remove text within (), {}, and [] along with the brackets
    processed_song_title = re.sub(r"[\(\{\[].*?[\)\}\]]", "", song_title).strip()
    
    # Extract the part before the hyphen if present
    if " - " in processed_song_title:
        processed_song_title = processed_song_title.split(" - ")[0].strip()

    # Validate session
    if not validate_session(session_key):
        return JsonResponse({"error": "Invalid or inactive session key."}, status=401)

    try:
        # Initialize Genius API client
        genius = lyricsgenius.Genius(
            os.getenv("GENIUS_CLIENT_ACCESS_TOKEN"),
            timeout=10,
            retries=3
        )

        def clean_lyrics(lyrics):
            """Remove everything before 'Lyrics' and return lyrics from the first verse."""
            # Remove everything before the word 'Lyrics'
            lyrics = re.split(r"(?i)Lyrics", lyrics, maxsplit=1)[-1].strip()
            # Remove any text before the first verse
            lyrics = re.split(r"\[.*?\]", lyrics, maxsplit=1)[-1].strip()
            return lyrics

        # Try fetching lyrics with the complete artist name
        try:
            song = genius.search_song(processed_song_title, artist_name)
            if song and song.lyrics:
                cleaned_lyrics = clean_lyrics(song.lyrics)
                return JsonResponse({"lyrics": cleaned_lyrics}, status=200)
        except Exception as e:
            print(f"Error fetching lyrics with full artist name: {e}")

        # If not found, split artist name by commas and try each part
        for artist in artist_name.split(","):
            artist = artist.strip()
            try:
                song = genius.search_song(processed_song_title, artist)
                if song and song.lyrics:
                    cleaned_lyrics = clean_lyrics(song.lyrics)
                    return JsonResponse({"lyrics": cleaned_lyrics}, status=200)
            except Exception as e:
                print(f"Error fetching lyrics for {processed_song_title} by {artist}: {e}")
                continue

        return JsonResponse({"error": "Lyrics not found."}, status=404)
    except Exception as e:
        print(f"Error fetching lyrics: {e}")
        return JsonResponse({"error": "Failed to fetch lyrics."}, status=500)

@api_view(['POST'])
def go_to_recommend_songs(request):
    """
    Redirect to the Recommend Songs page with the session key, emotion, and genres.
    """
    session_key = request.GET.get("session")
    data = json.loads(request.body)
    emotion = data.get("emotion")
    genres = data.get("genres")

    if not session_key or not emotion or not genres:
        return JsonResponse({"error": "Session key, emotion, and genres are required."}, status=400)

    return JsonResponse({
        "redirect_url": f"http://localhost:5173/recommend/songs?session={session_key}",
        "emotion": emotion,
        "genres": genres
    }, status=200)

# Updated Emotion to Spotify genres mapping
EMOTION_GENRE_MAPPING = {
    "Happy": ["pop", "dance", "electronic", "funk", "disco"],
    "Sad": ["acoustic", "blues", "classical", "soul", "folk"],
    "Angry": ["metal", "rock", "punk", "hardcore", "grunge"],
    "Surprise": ["indie", "alternative", "experimental", "psychedelic"],
    "Excited": ["hip-hop", "rap", "party", "trap", "reggaeton"],
    "Calm": ["ambient", "chill", "jazz", "lo-fi", "new-age"],
}

@api_view(['POST'])
def recommend_songs(request):
    """
    Recommend songs based on emotion and genres using Spotify's /search API.
    """
    session_key = request.GET.get("session")
    if not session_key:
        return JsonResponse({"error": "Session key is missing."}, status=400)

    try:
        data = json.loads(request.body)
        emotion = data.get("emotion")
        genres = data.get("genres")

        if not emotion or not genres:
            return JsonResponse({"error": "Emotion and genres are required."}, status=400)

        token = get_spotify_token_by_session(session_key)
        if not token:
            return JsonResponse({"error": "Invalid session or token not found"}, status=401)

        # Refresh token if expired
        if token.expires_at <= timezone.now():
            token = refresh_spotify_token(token)

        sp = spotipy.Spotify(auth=token.access_token)
        recommended_songs = []

        for genre in genres:
            results = sp.search(q=f"genre:{genre}", type="track", limit=50)  # Increase limit to 1000
            all_tracks = [
                {
                    "name": track["name"],
                    "artist": ", ".join(artist["name"] for artist in track["artists"]),
                    "album": track["album"]["name"],
                    "image": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
                    "track_id": track["id"],
                }
                for track in results["tracks"]["items"]
            ]
            recommended_songs.extend(all_tracks)

        recommended_songs = random.sample(recommended_songs, min(10, len(recommended_songs)))  # Select 5 random songs
        return JsonResponse({"songs": recommended_songs}, status=200)
    except spotipy.exceptions.SpotifyException as e:
        print(f"Spotify API error: {e}")
        return JsonResponse({"error": "Failed to fetch songs from Spotify."}, status=500)
    except Exception as e:
        print(f"Error in recommend_songs: {e}")
        return JsonResponse({"error": "Failed to recommend songs."}, status=500)

@api_view(['POST'])
def create_playlist(request):
    """Create a new playlist with the provided tracks."""
    session_key = request.GET.get("session")
    if not session_key:
        return JsonResponse({"error": "Session key is missing."}, status=400)

    try:
        data = json.loads(request.body)
        playlist_name = data.get("name")
        track_ids = data.get("track_ids", [])
        is_mood_changer = data.get("is_mood_changer", False)

        if not playlist_name:
            return JsonResponse({"error": "Playlist name is required."}, status=400)
        
        if not track_ids and not is_mood_changer:
            return JsonResponse({"error": "Track IDs are required."}, status=400)

        token = get_spotify_token_by_session(session_key)
        if not token:
            return JsonResponse({"error": "Invalid session or token not found"}, status=401)

        # Refresh token if expired
        if token.expires_at <= timezone.now():
            token = refresh_spotify_token(token)

        sp = spotipy.Spotify(auth=token.access_token)
        
        # Get the user's Spotify ID
        user_profile = sp.current_user()
        user_id = user_profile['id']
        
        # Handle mood changer playlist 
        if is_mood_changer:
            # Define a variety of positive genres to choose from
            positive_genres = [
                "happy", "feel-good", "summer", "dance", "disco", 
                "pop", "upbeat", "party", "sunshine", "energetic",
                "tropical", "groove", "funk", "soul", "positive",
                "power-pop", "euphoric", "motivational", "inspiring"
            ]
            
            # Use some of the existing tracks at the beginning for continuity (keeping the mood)
            negative_tracks = track_ids[:3]  # Start with current mood tracks
            
            # Select 3-5 random genres for this particular playlist
            selected_genres = random.sample(positive_genres, min(5, len(positive_genres)))
            
            # Build a pool of positive tracks from different genre searches
            positive_tracks_pool = []
            for genre in selected_genres:
                try:
                    # Search with a combination of terms to get varied results
                    search_query = f"genre:{genre}"
                    results = sp.search(q=search_query, type='track', limit=20)
                    genre_tracks = [track['id'] for track in results['tracks']['items']]
                    positive_tracks_pool.extend(genre_tracks)
                except Exception as e:
                    print(f"Error searching for genre {genre}: {e}")
                    continue
            
            # If we found positive tracks, randomly select some for the playlist
            if positive_tracks_pool:
                # Ensure we don't have duplicates
                positive_tracks_pool = list(set(positive_tracks_pool))
                # Select a random subset (aiming for around 7-10 tracks)
                positive_tracks = random.sample(
                    positive_tracks_pool, 
                    min(7, len(positive_tracks_pool))
                )
                
                # Create a transitional playlist: negative mood → positive mood
                track_ids = negative_tracks + positive_tracks
            else:
                # Fallback if genre searches didn't yield results
                fallback_results = sp.search(q='mood:happy', type='track', limit=7)
                fallback_tracks = [track['id'] for track in fallback_results['tracks']['items']]
                track_ids = negative_tracks + fallback_tracks
        
        # Create an empty playlist
        description = "Mood lifter playlist created by Aura" if is_mood_changer else f"Created from Aura on {timezone.now().strftime('%Y-%m-%d')}"
        created_playlist = sp.user_playlist_create(
            user=user_id,
            name=playlist_name,
            public=False,
            description=description
        )
        
        # Add tracks to the playlist (in batches of 100 if needed)
        playlist_id = created_playlist['id']
        for i in range(0, len(track_ids), 100):
            batch = track_ids[i:i+100]
            sp.playlist_add_items(playlist_id=playlist_id, items=batch)
        
        return JsonResponse({
            "success": True, 
            "playlist_id": playlist_id,
            "message": "Playlist created successfully!"
        }, status=201)
    
    except spotipy.exceptions.SpotifyException as e:
        print(f"Spotify API error: {e}")
        return JsonResponse({"error": f"Spotify API error: {str(e)}"}, status=500)
    except Exception as e:
        print(f"Error creating playlist: {e}")
        return JsonResponse({"error": f"Failed to create playlist: {str(e)}"}, status=500)
