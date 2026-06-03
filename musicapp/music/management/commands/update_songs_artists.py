from django.core.management import BaseCommand
import requests
import logging
import os

from ...models import Song, Artist


logger = logging.getLogger(__name__)


def fetch_track_data(track_id):
    token = os.getenv("SPOTIFY_TOKEN")
    track_url = f'https://api.spotify.com/v1/tracks/{track_id}'
    headers = {
        'Authorization': f'Bearer {token}',
    }
    params = {'market': 'UA'}

    try:
        response = requests.get(track_url, headers=headers, params=params, timeout=10)

        response.raise_for_status()

        return response.json()

    except requests.RequestException as e:
        logger.error("Failed to fetch track info for %s: %s", track_id, e)
        return None


def fetch_artist_data(artist_id):
    artist_url = "https://spotify-scraper3.p.rapidapi.com/api/artists/info"
    headers_scraper = {
        "x-rapidapi-key": os.getenv("RAPID_API_KEY"),
        "x-rapidapi-host": "spotify-scraper3.p.rapidapi.com"
    }
    params = {"id": artist_id}

    try:
        response = requests.get(artist_url, headers=headers_scraper, params=params, timeout=10)

        response.raise_for_status()

        return response.json()

    except requests.RequestException as e:
        logger.error("Failed to fetch artist info for %s: %s", artist_id, e)
        return None


class Command(BaseCommand):
    help = 'Update all songs with their corresponding artists'

    def handle(self, *args, **kwargs):
        songs = Song.objects.all()

        for song in songs:
            if song.artists.exists():
                logger.info("Song %s already has artists. Skipping.", song.name)
                continue

            logger.info("Updating song: %s", song.name)

            track_id = song.spotify_id

            track_data = fetch_track_data(track_id)
            if not track_data:
                continue

            artists_data = track_data.get('artists', [])

            artist_objs = []
            for artist_info in artists_data:
                artist_id = artist_info["id"]
                artist_name = artist_info["name"]

                artist = Artist.objects.filter(spotify_id=artist_id).first()
                if not artist:

                    artist_response = fetch_artist_data(artist_id)
                    if not artist_response:
                        continue

                    data = artist_response.json().get("data", {}).get("artist", {})
                    if data:
                        avatar_img = data["avatar_images"][0]["url"] if data.get("avatar_images") else None
                        header_img = data["header_images"][0]["url"] if data.get("header_images") else None

                        artist = Artist.objects.create(
                            spotify_id=artist_id,
                            name=artist_name,
                            profile_image=avatar_img,
                            detail_image=header_img,
                        )
                        logger.info("Created artist: %s", artist_name)
                    else:
                        logger.warning("No artist data found for %s", artist_name)
                        continue

                artist_objs.append(artist)

            if artist_objs:
                song.artists.set(artist_objs)
                logger.info("Updated song %s with %s artist(s).", song.name, len(artist_objs))
            else:
                logger.warning("No artists found for %s", song.name)

        logger.info("Finished updating songs.")
