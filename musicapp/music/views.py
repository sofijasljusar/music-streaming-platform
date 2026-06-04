from dotenv import load_dotenv

from django.views.generic import TemplateView, DetailView, CreateView
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth import login, get_user_model
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q

from .forms import SignUpForm, LoginForm
from .models import UserPlaylist, UserPlaylistSong, Song, Artist, ArtistAlbum, PlatformMix
from .constants import FEATURED_ARTIST_IDS, POPULAR_ARTIST_IDS, FEATURED_MIXES_IDS, FEATURED_RADIO_MIXES_IDS


User = get_user_model()

load_dotenv()


class HomeView(TemplateView):
    template_name = 'Home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # For now predefined artists
        # Todo: Later add feature for user upon sign up to search for artists he wants to listen to

        base_queryset = Song.objects.filter(
            artists__spotify_id__in=FEATURED_ARTIST_IDS
        ).exclude(
            Q(audio_url="https://example.com") | Q(lyrics="")  # only show songs with full data
        )

        context['new_releases'] = base_queryset.order_by('-release_date')[:6]
        context['trending_songs'] = base_queryset.order_by('-popularity')[:10]
        context['popular_artists'] = Artist.objects.filter(spotify_id__in=FEATURED_ARTIST_IDS)
        return context


class ArtistsView(LoginRequiredMixin, TemplateView):
    login_url = 'login'
    template_name = 'Artists.html'

    def get_context_data(self, **kwargs):
        """Add the artist's songs to the context."""
        context = super().get_context_data(**kwargs)

        context['popular_artists'] = Artist.objects.filter(spotify_id__in=POPULAR_ARTIST_IDS)

        return context


class ArtistDetailView(LoginRequiredMixin, DetailView):
    login_url = 'login'
    model = Artist
    template_name = 'ArtistDetail.html'
    context_object_name = 'artist'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        """Add the artist's songs to the context."""
        context = super().get_context_data(**kwargs)
        artist = self.object

        context['songs'] = artist.songs.all()[:10]
        context['albums'] = artist.albums.all()
        context['platform_mixes'] = artist.get_platform_mixes()  # artist playlists
        return context


class AlbumsView(LoginRequiredMixin, TemplateView):
    login_url = 'login'
    template_name = 'Albums.html'

    def get_context_data(self, **kwargs):
        """Add top mixes to the context."""
        context = super().get_context_data(**kwargs)

        context['radio_mixes'] = PlatformMix.objects.filter(spotify_id__in=FEATURED_RADIO_MIXES_IDS)
        context['mixes'] = PlatformMix.objects.filter(spotify_id__in=FEATURED_MIXES_IDS)

        return context


class PlaylistView(LoginRequiredMixin, TemplateView):
    login_url = 'login'
    template_name = 'Playlist.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        favorites_playlist = user.userplaylist_set.get(name="My favorites")
        context['playlist_songs'] = favorites_playlist.get_songs()
        return context


class PremiumView(TemplateView):
    template_name = 'Premium.html'


class SettingsView(LoginRequiredMixin, TemplateView):
    login_url = 'login'
    template_name = 'Settings.html'


class AboutView(TemplateView):
    template_name = 'AboutUs.html'


class OfficeView(TemplateView):
    template_name = 'Office.html'


class SongView(LoginRequiredMixin, DetailView):
    login_url = 'login'
    model = Song
    template_name = 'Song.html'
    context_object_name = 'song'
    pk_url_kwarg = 'id'


class AlbumDetailView(DetailView):
    model = ArtistAlbum
    template_name = "AlbumDetail.html"
    context_object_name = 'album'
    pk_url_kwarg = 'id'


class MixDetailView(DetailView):
    model = PlatformMix
    template_name = "MixDetail.html"
    context_object_name = 'mix'
    pk_url_kwarg = 'id'


class SignUpView(CreateView):
    model = User
    form_class = SignUpForm
    template_name = "signup.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect(self.success_url)


class LogInView(LoginView):
    template_name = "login.html"
    authentication_form = LoginForm

class SearchView(TemplateView):
    template_name = 'Search.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        search_query = self.request.GET.get('search_query', '')

        if search_query:
            songs = Song.objects.filter(name__icontains=search_query)
            artists = Artist.objects.filter(name__icontains=search_query)
            albums = ArtistAlbum.objects.filter(name__icontains=search_query)
        else:
            songs = []
            artists = []
            albums = []

        context['search_query'] = search_query
        context['songs'] = songs
        context['artists'] = artists
        context['albums'] = albums
        return context


class AddToFavoritesView(View):
    """Class-based view to add a song to the user's 'My favorites' playlist."""

    def post(self, request, song_id):
        user = request.user
        song = get_object_or_404(Song, id=song_id)

        favorites_playlist, created = UserPlaylist.objects.get_or_create(owner=user, name="My favorites")
        favorite_song = UserPlaylistSong.objects.filter(playlist=favorites_playlist, song=song).first()

        if not favorite_song:
            UserPlaylistSong.objects.create(playlist=favorites_playlist, song=song)
            return JsonResponse({'status': 'added'})

        else:
            favorite_song.delete()
            return JsonResponse({'status': 'removed'})
