import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import yt_dlp
import time

# 1. Authentication
def authenticate_spotify():
    sp_oauth = SpotifyOAuth(
        client_id=os.getenv('SPOTIPY_CLIENT_ID'),
        client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
        redirect_uri=os.getenv('SPOTIPY_REDIRECT_URI'),
        scope='user-library-read playlist-read-private'
    )

    # Step 1: Generate the authorization URL
    auth_url = sp_oauth.get_authorize_url()
    print(f'Please go to the following URL to authorize the application: {auth_url}')

    # Step 2: After visiting the URL and authorizing, you’ll be redirected to the redirect URI with a code parameter
    response = input('Paste the URL you were redirected to: ')

    # Step 3: Extract the code from the URL
    code = sp_oauth.parse_response_code(response)

    # Step 4: Get the access token
    token_info = sp_oauth.get_access_token(code)

    # Check if we successfully obtained an access token
    if token_info:
        print('Access token successfully obtained!')
        return spotipy.Spotify(auth=token_info['access_token'])
    else:
        print('Failed to obtain access token.')
        exit()

# 2. Spotify Playlist Handling
def get_user_playlists(sp):
    playlists = sp.current_user_playlists()
    all_playlists = []

    while playlists:
        for idx, playlist in enumerate(playlists['items'], start=len(all_playlists) + 1):
            print(f"{idx}. {playlist['name']} - ID: {playlist['id']}")
            all_playlists.append(playlist)
        
        if playlists['next']:
            playlists = sp.next(playlists)
        else:
            playlists = None
    
    return all_playlists

def select_playlist(sp, playlists):
    while True:
        choice = input('Choose the playlist you want to select: ')
        if choice.isdigit() and 1 <= int(choice) <= len(playlists):
            selected_playlist = playlists[int(choice) - 1]
            print(f"Selected Playlist: {selected_playlist['name']}")
            return selected_playlist['id']
        else:
            print('Please enter a valid number!')

def get_tracks_from_playlist(sp, playlist_id):
    tracks = sp.playlist_tracks(playlist_id)
    all_tracks = []

    while tracks:
        for idx, item in enumerate(tracks['items'], start=len(all_tracks) + 1):
            track_name = item['track']['name']
            artist_name = item['track']['artists'][0]['name']
            print(f"{idx}. {track_name} - Artist: {artist_name}")
            all_tracks.append(item)

        if tracks['next']:
            tracks = sp.next(tracks)
        else:
            tracks = None

    return all_tracks

def select_tracks(all_tracks):
    while True:
        choice = input("Enter numbers separated by commas (e.g., 1,2,3) or 'all' to select all: ").strip()
        if choice.lower() == 'all':
            return all_tracks
        choice_list = choice.split(',')
        valid_choices = []
        for number in choice_list:
            if number.isdigit() and 1 <= int(number) <= len(all_tracks):
                valid_choices.append(int(number))
            else:
                print("Please enter valid numbers separated by commas or 'all'!")
                break
        else:
            return [all_tracks[i - 1] for i in valid_choices]

# 3. YouTube Search and Download
def search_youtube(track_name, artist_name):
    search_query = f'ytsearch5:"{track_name}" "{artist_name}"'
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(search_query, download=False)
        if 'entries' in info_dict and info_dict['entries']:
            for entry in info_dict['entries']:
                video_title = entry.get('title', '').lower()
                if track_name.lower() in video_title and artist_name.lower() in video_title:
                    return entry['webpage_url']

        return info_dict['entries'][0]['webpage_url'] if info_dict['entries'] else None

def download_track(youtube_url, track_name, artist_name):
    if not youtube_url:
        print(f"Could not find a YouTube link for {track_name} by {artist_name}. Skipping download.")
        return

    download_folder = "SpotifyDownloads"
    os.makedirs(download_folder, exist_ok=True)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{download_folder}/{track_name} - {artist_name}.mp3',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f'Downloading: {track_name} by {artist_name}...')
            ydl.download([youtube_url])
            print(f'Download completed: {track_name} by {artist_name}')
    except Exception as e:
        print(f"Error downloading {track_name} by {artist_name}: {e}")

# Main execution
if __name__ == "__main__":
    sp = authenticate_spotify()

    playlists = get_user_playlists(sp)
    selected_playlist_id = select_playlist(sp, playlists)
    
    all_tracks = get_tracks_from_playlist(sp, selected_playlist_id)
    selected_tracks = select_tracks(all_tracks)

    for song in selected_tracks:
        youtube_url = search_youtube(song['track']['name'], song['track']['artists'][0]['name'])
        download_track(youtube_url, song['track']['name'], song['track']['artists'][0]['name'])
        time.sleep(1)  # To avoid overloading requests
