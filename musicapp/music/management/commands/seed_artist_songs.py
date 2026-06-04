import logging

from django.core.management import BaseCommand

from ...models import Artist, Song, ArtistAlbum
from ...utils import parse_release_date, milliseconds_to_timedelta
from ...services.spotify import SpotifyService
from ...services.lyrics import LyricsService
from ...scrapers.spotify_scraper import SpotifyScraper

logger = logging.getLogger(__name__)


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

        songs = SpotifyService.get_top_10_tracks(artist_id)
        for song in songs:
            self.process_song(song)


    def process_song(self, song):
        song_name = song["name"]
        logger.info(f"Processing song - {song_name}")

        artists = self.get_artists(song)
        lyrics = LyricsService.get_lyrics_from_genius(song_name, song["artists"][0]["name"])
        if lyrics and LyricsService.is_blocked_language(lyrics):
            logger.info("Skipping blocked language song: %s", song_name)
            return
        album, image_url = self.get_album_and_image(song)

        song, created = Song.objects.get_or_create(
            spotify_id=song["id"],
            defaults={
                "name": song_name,
                "album": album,
                "duration": milliseconds_to_timedelta(song["duration_ms"]),
                "release_date": parse_release_date(song["album"]["release_date"]),
                "audio_url": SpotifyScraper.get_track_preview_from_spotify(song["id"]),
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
                "release_date": parse_release_date(album_data["release_date"]),
                "image_url": album_data["images"][0]["url"],
            },
        )

        return album, None
