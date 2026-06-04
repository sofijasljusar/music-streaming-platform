import os
import base64
import requests
import logging

logger = logging.getLogger(__name__)

class SpotifyService:
    @staticmethod
    def get_spotify_api_token():
        client_id = os.getenv("SPOTIFY_ID")
        client_secret = os.getenv("SPOTIFY_SECRET")
        auth_str = f"{client_id}:{client_secret}"
        b64_auth = base64.b64encode(auth_str.encode()).decode()

        response = requests.post(
            'https://accounts.spotify.com/api/token',
            headers={
                'Authorization': f'Basic {b64_auth}',
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            data={'grant_type': 'client_credentials'},
            timeout=10,
        )
        response.raise_for_status()

        return response.json()['access_token']


    @staticmethod
    def get_top_10_tracks(artist_id):
        token = SpotifyService.get_spotify_api_token()
        market = 'UA'

        url = f'https://api.spotify.com/v1/artists/{artist_id}/top-tracks'
        headers = {
            'Authorization': f'Bearer {token}',
        }
        params = {
            'market': market
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()["tracks"]


    @staticmethod
    def get_artist_id(artist_name, token):
        url = "https://api.spotify.com/v1/search"

        headers = {
            "Authorization": f"Bearer {token}",
        }

        params = {
            "type": "artist",
            "q": artist_name,
            "limit": 1,
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        items = response.json()["artists"]["items"]
        if not items:
            return None

        return items[0]["id"]
