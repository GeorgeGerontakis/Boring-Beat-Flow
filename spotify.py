import requests
import json

def _get_song_uri(spotify_token, song_name):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {spotify_token}',
    }
    params = {
        'q': song_name,
        'type': 'track',
        'limit': 1
    }
    response = requests.get('https://api.spotify.com/v1/search', params=params, headers=headers)
    search_result = json.loads(response.text)
    if "tracks" in search_result:
        return search_result["tracks"]["items"][0]["uri"]
    else:
        if "error" in search_result:
            print(f"    [!] Spotify API Error: {search_result['error']['message']}")
        return None

def _get_playlist_id(spotify_token, playlist_name):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {spotify_token}',
    }
    response = requests.get('https://api.spotify.com/v1/me/playlists', headers=headers)
    search_result = json.loads(response.text)
    for playlist in search_result["items"]:
        if playlist["name"] == playlist_name:
            return playlist["id"]
    return None

def _add_songs_to_playlist(spotify_token, playlist_name, track_uris):
    playlist_id = _get_playlist_id(spotify_token, playlist_name)
    print(f"[*] Found playlist {playlist_name} -> {playlist_id}")
    uris = ""
    for uri in track_uris:
        uris += f'{uri},'
    print(uris)
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {spotify_token}',
    }
    params = {
        'playlist_id': playlist_id,
        'uris': uris[:-1],
    }
    response = requests.post(f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks', params=params, headers=headers)

def add_to_spotify_playlist(token, track_names, playlist_name):
    track_names = list(dict.fromkeys(track_names))
    uris = []
    for name in track_names:
        print(f"[*] Searching track: {name}")
        uri = _get_song_uri(token, name)
        if uri is None:
            print(f"    [-] No uri found for track {name}")
        else:
            print(f"    [*] Adding track {name} -> {uri}")
            uris.append(uri)
    _add_songs_to_playlist(token, playlist_name, uris)

def _get_auth_code(client_id):
    scope = "playlist-read-private playlist-modify-private" 
    url = f"https://accounts.spotify.com/authorize?client_id={client_id}&response_type=code&scope={scope}&redirect_uri=https://whatever" 
    auth_code_request = requests.get(url ,allow_redirects=True)
    redirect_url = auth_code_request.url
    print(redirect_url)
    while "?code=" not in redirect_url: 
        pass 
    code = redirect_url.split("?code=")[1] 
    return code 
 
def get_api_token(client_id, client_secret, redirect_uri): 
    code = _get_auth_code(client_id)
    authorization = requests.post( 
        "https://accounts.spotify.com/api/token", 
        auth=(client_id, client_secret), 
        data={ 
            "grant_type": "authorization_code", 
            "code": code, 
            "redirect_uri": redirect_uri 
        },         
    )
    print(authorization.text)
    authorization_JSON = authorization.json() 
    return authorization_JSON["access_token"]