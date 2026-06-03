from django.db.models import Q
from django.shortcuts import render

from django.views.generic import TemplateView, DetailView, CreateView, View
from .models import Song, Artist, ArtistAlbum, PlatformMix, UserPlaylist
from django.urls import reverse_lazy
from django.contrib.auth import authenticate, login
from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView
from .forms import SignUpForm, LoginForm
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
from django.http import JsonResponse
from django.views import View
from django.shortcuts import get_object_or_404
from .models import UserPlaylist, UserPlaylistSong, Song
from .constants import FEATURED_ARTIST_IDS, POPULAR_ARTIST_IDS
import requests
from googletrans import Translator
import base64
from dotenv import load_dotenv
import os
import datetime
from langdetect import detect
from bs4 import BeautifulSoup
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


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


class AlbumView(LoginRequiredMixin, TemplateView):
    login_url = 'login'
    template_name = 'Albums.html'

    def get_context_data(self, **kwargs):
        """Add top mixes to the context."""
        context = super().get_context_data(**kwargs)
        # Configure headless Chrome
        # options = Options()
        # options.add_argument("--headless")  # Optional: runs browser in background
        # options.add_argument("--disable-gpu")
        # options.add_argument("--window-size=1920,1080")
        # options.add_argument("--log-level=3")
        #
        # # Initialize WebDriver
        # driver = webdriver.Chrome(options=options)
        #
        # def scrape_playlist_tracks(playlist_id):
        #     playlist_url = f"https://open.spotify.com/playlist/{playlist_id}"
        #     driver.get(playlist_url)
        #
        #     # Let the page load (increase if needed)
        #     WebDriverWait(driver, 10).until(
        #         EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href^="/track/"]'))
        #     )
        #     time.sleep(2)
        #
        #     soup2 = BeautifulSoup(driver.page_source, "html.parser")
        #
        #     tracks = soup2.select('a[href^="/track/"]')
        #     print("Scraping tracks...")
        #     print(f"Total tracks {len(tracks)}")
        #     print(f"\n🎶 Tracks in Playlist ID: {playlist_id}\n")
        #
        #     songs = []
        #     for track_link in tracks:
        #         track_name = track_link.get_text(strip=True)
        #         track_href = track_link['href']
        #         track_id = track_href.split('/')[-1]
        #         song = Song.objects.filter(spotify_id=track_id).first()
        #         if not song:
        #             # Navigate up DOM to find related artist and album links
        #             track_container = track_link.find_parent('div')
        #             artist_link = track_container.find_next('a', href=lambda x: x and '/artist/' in x)
        #             album_link = track_container.find_next('a', href=lambda x: x and '/album/' in x)
        #
        #             artist_name = artist_link.get_text(strip=True) if artist_link else "Unknown Artist"
        #             artist_id = artist_link['href'].split('/')[-1] if artist_link else "No ID"
        #
        #             album_id = album_link['href'].split('/')[-1] if album_link else "No Album"
        #
        #             print(f"Track: {track_name} | Track ID: {track_id}")
        #             print(f"Artist: {artist_name} | Artist ID: {artist_id}")
        #             print(f"Album ID: {album_id}")
        #             print("-" * 40)
        #
        #             # SCRAPE ADDITIONAL SONG DETAILS FROM SPOTIFY + GENIUS
        #             token = get_spotify_api_token()
        #             market = 'UA'
        #
        #             track_url = f'https://api.spotify.com/v1/tracks/{track_id}'
        #             headers = {
        #                 'Authorization': f'Bearer {token}',
        #             }
        #             params = {
        #                 'market': market
        #             }
        #
        #             response = requests.get(track_url, headers=headers, params=params)
        #             if response.status_code == 200:
        #                 song = response.json()
        #                 print(f"Adding song - {track_name}")
        #                 duration = datetime.timedelta(milliseconds=song["duration_ms"])
        #                 release_date = song["album"]["release_date"]
        #                 if len(release_date) == 4:
        #                     release_date = datetime.datetime.strptime(release_date + "-01-01", "%Y-%m-%d").date()
        #
        #                 artist_objs = []
        #                 artist = Artist.objects.filter(spotify_id=artist_id).first()
        #                 if artist:
        #                     print(f"Artist {artist_name} already exists in the database.")
        #                 else:
        #                     artist_url = "https://spotify-scraper3.p.rapidapi.com/api/artists/info"
        #                     params = {"id": artist_id}
        #                     headers = {
        #                         "x-rapidapi-key": os.getenv("RAPID_API_KEY"),
        #                         "x-rapidapi-host": "spotify-scraper3.p.rapidapi.com"
        #                     }
        #
        #                     response = requests.get(artist_url, headers=headers, params=params)
        #                     print("HERE I AM!!!!")
        #                     print(response.json())
        #                     if response.status_code == 200:
        #                         data = response.json()["data"]["artist"]
        #                         if data:
        #                             avatar_img = None
        #                             header_img = None
        #                             if data["header_images"]:
        #                                 header_img = data["header_images"][0]["url"]
        #                             else:
        #                                 print("No header image")
        #                             if data["avatar_images"]:
        #                                 avatar_img = data["avatar_images"][0]["url"]
        #                             else:
        #                                 print("No header image")
        #
        #                             artist = Artist.objects.create(
        #                                 spotify_id=artist_id,
        #                                 profile_image=avatar_img,
        #                                 detail_image=header_img,
        #                                 name=artist_name,
        #                             )
        #                             print(f"Created artist {artist_name}.")
        #                         else:
        #                             print("No artist data found.")
        #                     else:
        #                         print(f"Failed to fetch artist info for {artist_name}.")
        #
        #                 artist_objs.append(artist)
        #
        #                 lyrics = get_lyrics_from_genius(track_name, artist_name)
        #                 if lyrics:
        #                     lang = detect(lyrics)
        #                     if lang == "ru":
        #                         "song_name is in russian - nonono"
        #                         continue
        #                 popularity = song["popularity"]
        #                 audio_url = get_track_preview_from_spotify(track_id)
        #                 album = None
        #                 image_url = None
        #
        #                 album_type = song["album"]["album_type"]
        #                 if album_type == "single":
        #                     image_url = song["album"]["images"][0]["url"]
        #                 elif album_type == "album":
        #                     album = ArtistAlbum.objects.filter(spotify_id=album_id).first()
        #
        #                     if not album:
        #                         print("Album not found. Creating...")
        #                         release_date = song["album"]["release_date"]
        #                         if len(release_date) == 4:
        #                             release_date = datetime.datetime.strptime(release_date + "-01-01",
        #                                                                       "%Y-%m-%d").date()
        #
        #                         album = ArtistAlbum.objects.create(
        #                             name=song["album"]["name"],
        #                             owner=Artist.objects.filter(spotify_id=artist_id).first(),
        #                             release_date=release_date,
        #                             image_url=song["album"]["images"][0]["url"],
        #                             spotify_id=album_id
        #                         )
        #
        #                 song = Song.objects.create(
        #                     spotify_id=track_id,
        #                     name=track_name,
        #                     album=album,
        #                     duration=duration,
        #                     release_date=release_date,
        #                     audio_url=audio_url,
        #                     lyrics=lyrics if lyrics else "",
        #                     image_url=image_url if image_url else None,
        #                     popularity=popularity
        #                 )
        #                 print(f"Created song {track_name}.")

        #                # BUG!!! forgot to set artists
        #
        #         else:
        #             print("Song exists")
        #         songs.append(song)
        #         print("Song added to mix")
        #     return songs
        #
        # def get_spotify_api_token():
        #     client_id = os.getenv("SPOTIFY_ID")
        #     client_secret = os.getenv("SPOTIFY_SECRET")
        #     auth_str = f"{client_id}:{client_secret}"
        #     b64_auth = base64.b64encode(auth_str.encode()).decode()
        #
        #     response = requests.post(
        #         'https://accounts.spotify.com/api/token',
        #         headers={
        #             'Authorization': f'Basic {b64_auth}',
        #             'Content-Type': 'application/x-www-form-urlencoded'
        #         },
        #         data={'grant_type': 'client_credentials'}
        #     )
        #
        #     return response.json()['access_token']
        #
        # def get_track_preview_from_spotify(song_id):
        #     track_url = f"https://open.spotify.com/track/{song_id}"
        #
        #     response = requests.get(track_url)
        #
        #     if response.status_code == 200:
        #         soup = BeautifulSoup(response.content, 'html.parser')
        #
        #         og_audio_tag = soup.find('meta', property='og:audio')
        #
        #         if og_audio_tag:
        #             url = og_audio_tag.get('content')
        #             print(url)
        #             return url
        #         else:
        #             print("Audio URL not found in the meta tags.")
        #             return "https://fakeurl.com"
        #     else:
        #         print(f"Error: Unable to fetch the page. Status code: {response.status_code}")
        #         return "https://fakeurl.com"
        #
        # def get_lyrics_from_genius(song_title, artist_name):
        #
        #     if song_title == "Забий":
        #         song_title = "Let It Go"
        #     elif song_title == "ДІВ ЧИНА":
        #         song_title = "Girl"
        #     elif song_title == "Вишнi":
        #         song_title = "Cherries"
        #     else:
        #         lang = detect(song_title)
        #         if lang != "en":
        #             translator = Translator()
        #             song_title = translator.translate(song_title, src='uk', dest='en').text
        #     search_for = f"{song_title} {artist_name}"
        #     print(search_for)
        #
        #     search_endpoint = "https://api.genius.com/search"
        #     headers = {
        #         'Authorization': f'Bearer {os.getenv("GENIUS_TOKEN")}',
        #     }
        #     params = {
        #         'q': search_for
        #     }
        #
        #     response = requests.get(search_endpoint, headers=headers, params=params)
        #     if response.status_code == 200 and response.json()["response"]["hits"]:
        #         print(artist_name)
        #         print(response.json()["response"]["hits"][0]["result"]["artist_names"])
        #         print(artist_name in response.json()["response"]["hits"][0]["result"]["artist_names"])
        #         if response.json()["response"]["hits"][0]["result"]["lyrics_state"] == "complete" \
        #                 and artist_name in response.json()["response"]["hits"][0]["result"]["artist_names"]:
        #             base = "https://genius.com"
        #             endpoint = response.json()["response"]["hits"][0]["result"]["path"]
        #             link = base + endpoint
        #             print(link)
        #             header = {
        #                 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0"}
        #             response = requests.get(url=link, headers=header)
        #
        #             contents = response.text
        #             soup = BeautifulSoup(contents, "html.parser")
        #             lyrics_container = soup.find_all(class_="Lyrics__Container-sc-78fb6627-1 hiRbsH")
        #
        #             text = "\n".join([block.get_text(separator="\n") for block in lyrics_container]).splitlines()
        #             lyrics = "\n".join(text[2:])
        #             print(lyrics)
        #
        #             return lyrics
        #         return ""
        #
        # # SCRAPE MIXES PAGE
        # try:
        #     # Open the Spotify section page
        #     url = "https://open.spotify.com/section/0JQ5DAuChZYPe9iDhh2mJz"
        #     driver.get(url)
        #     print("hello")
        #     # Wait until at least one playlist title is present
        #     WebDriverWait(driver, 10).until(
        #         EC.presence_of_element_located((By.CSS_SELECTOR, 'p[data-encore-id="cardTitle"]'))
        #     )
        #
        #     # Parse page source with BeautifulSoup
        #     soup1 = BeautifulSoup(driver.page_source, "html.parser")
        #     # Get all card containers
        #     cards = soup1.find_all("div", {"data-encore-id": "card"})[7:]
        #     print(len(cards))
        #     print("🎵 Extracted Playlist Cards:\n")
        #     playlist_ids = []
        #     for card in cards:
        #         # Extract title
        #         title_tag = card.find("p", {"data-encore-id": "cardTitle"})
        #         playlist_title = title_tag.get_text(strip=True) if title_tag else "No Title"
        #         to_skip = ["Max Korzh Radio", "KRBK Radio"]
        #         if playlist_title in to_skip:
        #             print("skipping " + playlist_title)
        #             continue
        #         # Extract image
        #         img_tag = card.find("img", {"data-testid": "card-image"})
        #         img_url = img_tag["src"] if img_tag else None
        #
        #         link_tag = card.find("a", href=True)
        #         playlist_id = link_tag["href"].split("/")[-1] if link_tag and "/playlist/" in link_tag[
        #             "href"] else "No ID"
        #         playlist_ids.append(playlist_id)
        #         print(f"Title: {playlist_title}")
        #         print(f"Image URL: {img_url}")
        #         print(f"Playlist ID: {playlist_id}")
        #         print("-" * 50)
        #         # SCRAPE SONGS FROM PLAYLIST PAGE
        #         mix_songs = scrape_playlist_tracks(playlist_id)
        #         mix, created = PlatformMix.objects.get_or_create(
        #             spotify_id=playlist_id,
        #             defaults={
        #                 "name": playlist_title,
        #                 "image_url": img_url
        #             }
        #         )
        #
        #         if created:
        #             mix.songs.set(mix_songs)  # use .set() to assign all at once
        #         else:
        #             mix.songs.add(*mix_songs)
        #
        #     print(playlist_ids)
        #     print(f"Total mixes loaded {len(playlist_ids)}")
        # #
        # finally:
        #     driver.quit()

        radio_mixes_ids = ['37i9dQZF1E4l2ioIaCjhu0', '37i9dQZF1E4l6urr0WyrHk', '37i9dQZF1E4wuO62icjSo9',
                           '37i9dQZF1E4tLXl1ytNjGw',
                           '37i9dQZF1E4A8y674xzcYv', '37i9dQZF1E4vm60o07iwlG', '37i9dQZF1E4noT0MbKz5Ed',
                           '37i9dQZF1E4DTZUur7HqeC',
                           '37i9dQZF1E4xO7AcESjSyV', '37i9dQZF1E4Bz1Tyga0dyF', '37i9dQZF1E4xxHdVdUnARi',
                           '37i9dQZF1E4AfgteCrizQG',
                           '37i9dQZF1E4vkBCi0dJzdI', '37i9dQZF1E4xQ4S5eUfiuo', '37i9dQZF1E4FCYxweFnGWe',
                           '37i9dQZF1E4sPFmlETtBHH',
                           '37i9dQZF1E4yl1BBzACV3o', '37i9dQZF1E4wXrG4w9c53u', '37i9dQZF1E4yQINTazcB01',
                           '37i9dQZF1E4ptINQIygp3c']
        mixes_ids = ['37i9dQZF1DX5ECfKO3L7Vd', '37i9dQZF1DX1V3tM4cuX0v', '37i9dQZF1DXcU2mDfNlJqd',
                     '37i9dQZF1DWZU4i93guc1c', '37i9dQZF1DWTtjLYc6QFF2', '37i9dQZF1DX69uAEiqiuHZ',
                     '37i9dQZF1DX9lOLSAzbbCv', '37i9dQZF1DX5zxOB6DkdZY', '37i9dQZF1DX2X2YHi92QqA',
                     '37i9dQZF1DWUxthdWUs4N4', '37i9dQZF1DWW5PAbWFxH0K']
        context['radio_mixes'] = PlatformMix.objects.filter(spotify_id__in=radio_mixes_ids)
        context['mixes'] = PlatformMix.objects.filter(spotify_id__in=mixes_ids)
        # context['albums'] = 0

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
