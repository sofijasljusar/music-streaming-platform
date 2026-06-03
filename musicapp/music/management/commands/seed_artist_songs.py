import logging
import os
import requests
import base64
import datetime
from bs4 import BeautifulSoup
from langdetect import detect
from googletrans import Translator
import time
import random

from django.core.management import BaseCommand

from ...models import Artist, Song, ArtistAlbum

logger = logging.getLogger(__name__)

MISSING_AUDIO_URL = "https://example.com"
TRANSLATION_EXCEPTIONS = {
    "Забий": "Let It Go",
    "ДІВ ЧИНА": "Girl",
    "Вишнi": "Cherries",
    "27": "27",
}

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


def get_top_10_tracks(artist_id):
    token = get_spotify_api_token()
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


def get_lyrics_from_genius(song_title, artist_name):
    song_title = TRANSLATION_EXCEPTIONS.get(song_title, song_title)

    if detect(song_title) != "en":
        song_title = Translator().translate(
            song_title,
            src="uk",
            dest="en",
        ).text

    response = requests.get(
        "https://api.genius.com/search",
        headers={
            "Authorization": f'Bearer {os.getenv("GENIUS_TOKEN")}',
        },
        params={
            "q": f"{song_title} {artist_name}",
        },
        timeout=10,
    )
    response.raise_for_status()

    hits = response.json()["response"]["hits"]

    if not hits:
        return ""

    result = hits[0]["result"]

    if result["lyrics_state"] != "complete":
        return ""

    if artist_name not in result["artist_names"]:
        return ""

    lyrics_page = requests.get(
        f'https://genius.com{result["path"]}',
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) "
                "Gecko/20100101 Firefox/131.0"
            )
        },
        timeout=10,
    )
    lyrics_page.raise_for_status()

    soup = BeautifulSoup(lyrics_page.text, "html.parser")

    containers = soup.find_all(
        class_="Lyrics__Container-sc-78fb6627-1 hiRbsH"
    )

    lyrics_lines = "\n".join(
        block.get_text(separator="\n")
        for block in containers
    ).splitlines()

    return "\n".join(lyrics_lines[2:])


def get_song_url_from_soundcloud(song_title, artist_name):
    scraper_url = "https://spotify-scraper.p.rapidapi.com/v1/track/download/soundcloud"
    querystring = {"track": f"{song_title} {artist_name}", "quality": "sq"}
    headers = {
        "x-rapidapi-key": os.getenv("RAPID_API_KEY"),
        "x-rapidapi-host": "spotify-scraper.p.rapidapi.com"
    }

    response = requests.get(scraper_url, headers=headers, params=querystring, timeout=10)
    scraper_data = response.json()
    if "soundcloudTrack" in scraper_data:
        return scraper_data["soundcloudTrack"]["audio"][0]["url"]
    else:
        return MISSING_AUDIO_URL


def get_track_preview_from_spotify(song_id):
    track_url = f"https://open.spotify.com/track/{song_id}"

    response = requests.get(track_url, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')

    og_audio_tag = soup.find('meta', property='og:audio')

    if not og_audio_tag:
        logger.warning(
            "Audio URL for song %s not found in meta tags.",
            song_id,
        )
        return MISSING_AUDIO_URL

    return og_audio_tag.get("content", MISSING_AUDIO_URL)


class Command(BaseCommand):
    help = 'Populate artist songs'

    def add_arguments(self, parser):
        parser.add_argument(
            "artist_id",
            type=str,
            help="Spotify artist ID",
        )


    def handle(self, *args, **kwargs):
        artist_id = kwargs["artist_id"]

        songs = get_top_10_tracks(artist_id)
        for song in songs:
            self.process_song(song)

        self.update_audio_previews()

    def process_song(self, song):
        song_name = song["name"]
        logger.info(f"Processing song - {song_name}")

        artists = self.get_artists(song)
        lyrics = get_lyrics_from_genius(song_name, song["artists"][0]["name"])
        if lyrics and detect(lyrics):
            logger.info("Skipping Russian song: %s", song_name)
            return
        album, image_url = self.get_album_and_image(song)

        song, created = Song.objects.get_or_create(
            spotify_id=song["id"],
            defaults={
                "name": song_name,
                "album": album,
                "duration": datetime.timedelta(
                    milliseconds=song["duration_ms"]
                ),
                "release_date": self.parse_release_date(song["album"]["release_date"]),
                "audio_url": get_track_preview_from_spotify(song["id"]),
                "lyrics": lyrics or "",
                "image_url": image_url,
                "popularity": song["popularity"],
            },
        )

        if created:
            song.artists.set(artists)
        else:
            song.artists.add(*artists)

            if lyrics and not song.lyrics:
                song.lyrics = lyrics
                song.save(update_fields=["lyrics"])


    def get_artists(self, song):
        artists = []

        for artist in song["artists"]:
            artist, _ = Artist.objects.get_or_create(
                spotify_id=artist["id"],
                defaults={"name": artist["name"]}
            )
            artists.append(artist)

        return artists


    def get_album_and_image(self, song):
        album_data = song["album"]

        if album_data["album_type"] == "single":
            return None, album_data["images"][0]["url"]

        album, _ = ArtistAlbum.objects.get_or_create(
            spotify_id=album_data["id"],
            defaults={
                "name": album_data["name"],
                "release_date": self.parse_release_date(album_data["release_date"]),
                "image_url": album_data["images"][0]["url"],
            },
        )

        return album, None


    def parse_release_date(self, value):
        if len(value) == 4:
            value = f"{value}-01-01"

        return datetime.datetime.strptime(
                value,
                "%Y-%m-%d",
            ).date()


    def update_audio_previews(self):
        logger.info("Updating audio previews...")

        for song in Song.objects.all():
            try:
                audio_url = get_track_preview_from_spotify(song.spotify_id)

                if audio_url:
                    song.audio_url = audio_url
                    song.save(update_fields=["audio_url"])

                time.sleep(random.uniform(1, 3))

            except requests.RequestException as e:
                logger.warning(
                    "Failed preview update for %s: %s",
                    song.spotify_id,
                    e,
                )