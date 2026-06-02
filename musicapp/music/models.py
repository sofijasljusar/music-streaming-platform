from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from slugify import slugify
from datetime import timedelta


class Genre(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Artist(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=150, null=False, unique=True)
    genres = models.ManyToManyField(Genre, related_name="artists", blank=True)
    profile_image = models.URLField(blank=True, null=True)
    detail_image = models.URLField(blank=True, null=True)
    spotify_id = models.CharField(max_length=50, unique=True)

    def get_absolute_url(self):
        """Returns the URL for the artist's detail page using slug."""
        return reverse('artist_detail', args=[self.slug])

    def save(self, *args, **kwargs):
        """Automatically generate a slug from the artist's name if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_profile_image(self):
        """Returns the profile image URL, or the default placeholder if None."""
        return self.profile_image or "/static/musicapp/images/artist-placeholder.jpg"

    def get_detail_image(self):
        """Returns the detail image URL, or the default placeholder if None."""
        return self.detail_image or "/static/musicapp/images/detail-placeholder.jpg"

    def get_platform_mixes(self):
        """Returns all platform mixes that contain songs by this artist."""
        return PlatformMix.objects.filter(songs__artists=self).distinct()

    def __str__(self):
        return self.name


class SongCollection(models.Model):
    name = models.CharField(max_length=100)
    image_url = models.URLField(blank=True, null=True)

    def get_total_duration(self):
        total_seconds = sum(song.duration.total_seconds() for song in self.get_songs())
        return timedelta(seconds=total_seconds)

    def get_amount_of_songs(self):
        return self.get_songs().count()

    def get_songs(self):
        raise NotImplementedError("Subclasses must implement the get_songs method.")

    def get_image(self):
        """Returns the image URL, or the default placeholder if None."""
        return self.image_url or "/static/musicapp/images/playlist-placeholder.jpg"

    def __str__(self):
        return self.name


class ArtistAlbum(SongCollection):
    owner = models.ForeignKey('Artist', on_delete=models.CASCADE, related_name="albums")
    release_date = models.DateField()
    genres = models.ManyToManyField(Genre, related_name="albums", blank=True)
    spotify_id = models.CharField(max_length=50, unique=True)

    def get_songs(self):
        return self.songs.all()


class Song(models.Model):
    name = models.CharField(max_length=100)
    artists = models.ManyToManyField(Artist, related_name='songs', blank=True)  # todo: handle deletion of all artists for song
    album = models.ForeignKey(ArtistAlbum, related_name='songs',  on_delete=models.CASCADE, null=True, blank=True)
    duration = models.DurationField()
    release_date = models.DateField()
    audio_url = models.URLField(max_length=500)
    lyrics = models.TextField(blank=True, null=False)
    genres = models.ManyToManyField(Genre, related_name="songs", blank=True)
    image_url = models.URLField(blank=True, null=True)
    popularity = models.PositiveIntegerField(default=0)
    spotify_id = models.CharField(max_length=50, unique=True)

    def get_image(self):
        """Returns the image URL, or the default placeholder if None."""
        if self.image_url:
            return self.image_url
        if self.album and self.album.image_url:
            return self.album.image_url
        return "/static/musicapp/images/song-placeholder.jpg"

    def __str__(self):
        artists_names = ", ".join(artist.name for artist in self.artists.all())
        return f"{self.name} by {artists_names}"


class PlatformMix(SongCollection):
    owner = models.CharField(max_length=255, default="Melonix")
    songs = models.ManyToManyField(Song, related_name='mixes')
    genres = models.ManyToManyField(Genre, related_name="mixes", blank=True)
    spotify_id = models.CharField(max_length=50, unique=True, null=True)

    def get_image(self):
        """Returns the image URL, or the default placeholder if None."""
        return self.image_url or "/musicapp/images/Trending songs mix.png"

    def get_songs(self):
        return self.songs.all()


class UserPlaylist(SongCollection):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def get_songs(self):
        return Song.objects.filter(userplaylistsong__playlist=self)

    def get_image(self):
        """Return the image of the first song in the playlist, or the default placeholder if none."""
        first_song = self.get_songs().first()
        if first_song:
            return first_song.get_image()  # Use the first song's image, whether it's the song or album image
        return "/static/musicapp/images/playlist-placeholder.jpg"  # Fallback to playlist placeholder


class UserPlaylistSong(models.Model):
    playlist = models.ForeignKey(UserPlaylist, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    date_added = models.DateField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['playlist', 'song'], name='unique_playlist_song')
        ]
