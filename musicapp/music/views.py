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

        # official spotify API
        # top_ukrainian_artists = ["6wbEgVlGqWb4I9tbMluu5Q",  # spotify ids
        #                          "5RqIkHQnXRZlm1ozfSS1IO",
        #                          "5BwbVAdT6rFF2vGVE8su2y",
        #                          "6NTzEgUmN1PIBIYEHhf1kS",
        #                          "2c3PFZtun8HemDbDfRPV6G",
        #                          "7wl1m5vgWkCP3cqYVj2noM",
        #                          "6l5IEx62Nsc2k1QyfaWvEz",
        #                          ]
        #
        # top_ukrainian_artists = ["11sIz9STeD6yVSuBaD8nMW"]
        #
        # names = []
        #
        # # SCRAPER FOR IMAGES (INCLUDING HEADER IMAGE)
        # for artist_id in top_ukrainian_artists:
        #     print("HELLOOO")
        #     url = "https://spotify-scraper3.p.rapidapi.com/api/artists/info"
        #     params = {"id": artist_id}
        #     headers = {
        #         "x-rapidapi-key": os.getenv("RAPID_API_KEY"),
        #         "x-rapidapi-host": "spotify-scraper3.p.rapidapi.com"
        #     }
        #
        #     response = requests.get(url, headers=headers, params=params)
        #     print(response)
        #     if response.status_code == 200:
        #         data = response.json()["data"]["artist"]
        #         name = data["name"]
        #         avatar_img = data["avatar_images"][0]["url"]
        #         header_img = data["header_images"][0]["url"]
        #         names.append(name)
        #         artist, created = Artist.objects.get_or_create(
        #             name=name,
        #             defaults={
        #                 "profile_image": avatar_img,
        #                 "detail_image": header_img,
        #                 "spotify_id": artist_id,
        #             }
        #         )
        #
        #         if created:
        #             print("Artist was just added to the database!")
        #         else:
        #             print("Artist already existed, maybe update info if needed.")
        #
        #         print("Info:"
        #               "\nname- " + name +
        #               "\navatar_img- " + avatar_img +
        #               "\nheader_img- " + header_img)
        #
        # print(names)

        # For now predefines artists
        # todo: Later add feature for user upon sign up to search for artists he wants to listen to
        names = ['MONATIK', 'Скрябін', 'Klavdia Petrivna', 'Okean Elzy', 'Boombox', 'DOROFEEVA', 'Wellboy']

        # context["form"] = CustomUserCreationForm()
        context['new_releases'] = Song.objects.filter(
            artists__name__in=names
        ).exclude(
            Q(audio_url="https://example.com") | Q(lyrics="")
        ).order_by('-release_date')[:6]
        # context['new_releases'] = Song.objects.order_by('-release_date')[:6]  # Fetch latest 6 songs
        context['trending_songs'] = Song.objects.filter(
            artists__name__in=names
        ).exclude(
            Q(audio_url="https://example.com") | Q(lyrics="")
        ).order_by('-popularity')[:10]
        # context['trending_songs'] = Song.objects.order_by('-release_date')[:10]  # Example logic for trending
        context['popular_artists'] = Artist.objects.filter(name__in=names)  # Fetch first 7 artists
        return context


class ArtistsView(LoginRequiredMixin, TemplateView):
    login_url = 'login'
    template_name = 'Artists.html'

    def get_context_data(self, **kwargs):
        """Add the artist's songs to the context."""
        context = super().get_context_data(**kwargs)

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
                data={'grant_type': 'client_credentials'}
            )

            return response.json()['access_token']

        def get_artist_id(artist_name):
            token = get_spotify_api_token()
            market = 'UA'

            url = f'https://api.spotify.com/v1/search'
            headers = {
                'Authorization': f'Bearer {token}',
            }
            params = {
                'type': "artist",
                'q': artist_name
            }

            response = requests.get(url, headers=headers, params=params).json()["artists"]["items"][0]["id"]
            print(response)

        def get_top_chart():
            date = datetime.datetime.now().date()
            url = "https://www.billboard.com/charts/artist-100/" + str(date)
            header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0"}
            response = requests.get(url=url, headers=header)

            contents = response.text
            soup = BeautifulSoup(contents, "html.parser")

            title_elements = soup.select(selector=".chart-results-list li h3")
            titles = [title.getText().strip() for title in title_elements]
            return titles

        # top_names = get_top_chart()
        # artist_ids = [get_artist_id(name) for name in top_names]
        artist_ids = [
            "4oUHIQIBe0LHzYfvXNW4QM",
            "2YZyLoL8N0Wb9xBt1NhZWg",
            "74KM79TiuVKeVCqs8QtB0B",
            "7tYKF4w9nC0nq9CsPZTHyP",
            "7GlBOeep6PqTfFi59PTUUN",
            "1HY2Jd0NmPuamShAr6KMms",
            "33qOK5uJ8AR2xuQQAhHump",
            "3TVXtAsR1Inumwj472S9r4",
            "19k8AgwwTSxeaxkOuCQEJs",
            "246dkjvS1zLTtiykXe5h60",
            "6qqNVTkY8uBg9cP3Jd7DAH",
            "4tuJ0bMpJh08umKkEXKUI5",
            "22wbnEMDvgVIAGdFeek6ET",
            "1Xyo4u8uXC1ZmMpatF05PJ",
            "06HL4z0CvFAxyc27GXpf02",
            "718COspgdWOnwOFpJHRZHS",
            "4E2rKHVDssGJm2SCDOMMJB",
            "0du5cEVh5yTK9QJze8zA0C",
            "3y2cIKLjiOlp1Np37WiUdH",
            "66CXWjxzNUsdJxJ2JdwvnR",
            "3gBZUcNeVumkeeJ19CY2sX",
            "6qxpnaukVayrQn6ViNvu9I",
            "4LEiUm1SRbFMgfqnQTwUbQ",
            "4q3ewBCX7sLwd24euuV69X",
            "0fTSzq9jAh4c36UVb4V7CB",
            "4V8LLVI7PbaPR0K2TGSxFF",
            "08GQAI4eElDnROBrJRGE0X",
            "45dkTj5sMRSjrmBSBeiHym",
            "40ZNYROS4zLfyyBSs2PGe2",
            "6eUKZXaKkcviH0Ku9w2n3V",
            "3win9vGIxFfBRag9S63wwf",
            "2FXC3k01G6Gw61bmprjgqS",
            "4YLtscXsxbVgi031ovDDdh",
            "67FB4n52MgexGQIG8s0yUH",
            "3bO19AOone0ubCsfDXDtYt",
            "2sSGPbdZJkaSE2AbcGOACx",
            "25uiPmTg16RbhZWAqwLBy5",
            "5YGY8feqx7naU7z4HrwZM6",
            "699OTQXzgjhIYAHMy9RyPD",
            "6pV5zH2LzjOUHaAvENdMMa",
            "2ye2Wgw4gimLv2eAKyk1NB",
            "0nnBZ8FXWjG9wZgM2cpfeb",
            "6olE6TJLqED3rqDCT0FyPh",
            "6XyY86QOPPrYVGvF9ch6wz",
            "1dfeR4HaWDbWqFHLkxsg1d",
            "4FGPzWzgjURDNT7JQ8pYgH",
            "7bXgB6jMjp9ATFy66eO08Z",
            "5eumcnUkdmGvkvcsx1WFNG",
            "2d0hyoQ5ynDBnkvAbJKORj",
            "711MCceyCBcFnzjGY4Q7Un",
            "0NIPkIjTV8mB795yEIiPYL",
            "00FQb4jTyendYWaN8pK0wa",
            "2qoQgPAilErOKCwE2Y8wOG",
            "2QMsj4XJ7ne2hojxt6v5eb",
            "1scVfBymTr3CeZ4imMj1QJ",
            "2RQXRUsr4IW1f3mKyKsy4B",
            "2h93pZq0e7k5yf4dywlkpM",
            "1bdnGJxkbIIys5Jhk1T74v",
            "3oSJ7TBVCWMDMiYjXNiCKE",
            "6ltzsmQQbmdoHHbLZ4ZN25",
            "4Z8W4fKeB5YxbusRsdQVPb",
            "4TMHGUX5WI7OOm53PqSDAT",
            "3AA28KZvwAUcZuOKwyblJQ",
            "7gW0r5CkdEUMm42w9XpyZO",
            "2n2RSaZqBuUUukhbLlpnE6",
            "3fMbdgg4jU18AjLCKBhRSm",
            "2yLzlEFtIS0Q9UkyBZdQA7",
            "2x9SpqnPi8rlE9pjHBwmSC",
            "40Yq4vzPs9VNUrIBG5Jr2i",
            "6BRxQ8cD3eqnrVj6WKDok8",
            "4ytkhMSAnrDP8XzRNlw9FS",
            "3eVa5w3URK5duf6eyVDbu9",
            "3PhoLpVuITZKcymswpck5b",
            "4MoAOfV4ROWofLG3a3hhBN",
            "4NYMUsIcUUsBHbV9DICa5x",
            "4gzpq5DPGxSnKTe4SA8HAU",
            "0Y5tJX1MQlPlqiwlOH1tJY",
            "1RyvyyTE3xzB2ZywiAwp0i",
            "5Ppie0uPnbnvGBYRwYmlt0",
            "43sZBwHjahUvgbx1WNIkIz",
            "3FfvYsEGaIb52QPXhg4DcH",
            "4Ga1P7PMIsmqEZqhYZQgDo",
            "1iCnM8foFssWlPRLfAbIwo",
            "7Ez6lTtSMjMf2YSYpukP1I",
            "0ys2OFYzWYB5hRDLCsBqxt",
            "5QNm7E7RU2m64l6Gliu8Oy",
            "0avMDS4HyoCEP6RqZJWpY2",
            "6zLBxLdl60ekBLpawtT63I",
            "2hlmm7s2ICUX0LVIhVFlZQ",
            "0ECwFtbIWEVNwjlrfc6xoL",
            "1WaFQSHVGZQJTbf0BdxdNo",
            "5f7VJjfbwm532GiveGC0ZK",
            "3IYUhFvPQItj6xySrBmZkd",
            "0oSGxfWSnnOXhD2fKuz2Gy",
            "0C8ZW7ezQVs4URX5aX7Kqx",
            "4G9NDjRyZFDlJKMRL8hx3S",
            "2HPaUgqeutzr3jx5a9WyDV",
            "6l3HvQ5sa6mXTsMTB19rO5",
            "1UTPBmNbXNTittyMJrNkvw",
            "50co4Is1HCEo8bhOyUWKpn"
        ]

        # for artist_id in artist_ids:
        #     url = "https://spotify-scraper3.p.rapidapi.com/api/artists/info"
        #     params = {"id": artist_id}
        #     headers = {
        #         "x-rapidapi-key": os.getenv("RAPID_API_KEY"),
        #         "x-rapidapi-host": "spotify-scraper3.p.rapidapi.com"
        #     }
        #
        #     response = requests.get(url, headers=headers, params=params)
        #     print(response.json())
        #     if response.status_code == 200:
        #         data = response.json()["data"]["artist"]
        #         if data:
        #             name = data["name"]
        #             avatar_img = data["avatar_images"][0]["url"]
        #             header_img = None
        #             if data["header_images"]:
        #                 header_img = data["header_images"][0]["url"]
        #             else:
        #                 print("No header image")
        #             artist, created = Artist.objects.get_or_create(
        #                 spotify_id=artist_id,
        #                 defaults={
        #                     "profile_image": avatar_img,
        #                     "detail_image": header_img,
        #                     "name": name,
        #                 }
        #             )
        #
        #             if created:
        #                 print("Artist was just added to the database!")
        #             else:
        #                 print("Artist already existed, maybe update info if needed.")
        #         else:
        #             print("No artist")

        context['popular_artists'] = Artist.objects.filter(spotify_id__in=artist_ids)
        return context


class ArtistDetailView(LoginRequiredMixin, DetailView):
    login_url = 'login'
    model = Artist
    template_name = 'ArtistDetail.html'
    context_object_name = 'artist'
    slug_field = 'slug'  # use slug for lookup
    slug_url_kwarg = 'slug'  # match url parameter

    def get_context_data(self, **kwargs):
        """Add the artist's songs to the context."""
        context = super().get_context_data(**kwargs)
        artist_id = self.object.spotify_id
        print(artist_id)
        artist_name = self.object.name

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
                data={'grant_type': 'client_credentials'}
            )

            return response.json()['access_token']

        def get_top_10_tracks():
            token = get_spotify_api_token()
            market = 'UA'

            url = f'https://api.spotify.com/v1/artists/{artist_id}/top-tracks'
            headers = {
                'Authorization': f'Bearer {token}',
            }
            params = {
                'market': market
            }

            response = requests.get(url, headers=headers, params=params)
            print(response)
            if response.status_code == 200:
                return response.json()["tracks"]

        def get_lyrics_from_genius(song_title):

            if song_title == "Забий":
                song_title = "Let It Go"
            elif song_title == "ДІВ ЧИНА":
                song_title = "Girl"
            elif song_title == "Вишнi":
                song_title = "Cherries"
            elif song_title == "27":
                song_title = "27"
            else:
                lang = detect(song_title)
                if lang != "en":
                    translator = Translator()
                    song_title = translator.translate(song_title, src='uk', dest='en').text
            search_for = f"{song_title} {artist_name}"
            print(search_for)

            search_endpoint = "https://api.genius.com/search"
            headers = {
                'Authorization': f'Bearer {os.getenv("GENIUS_TOKEN")}',
            }
            params = {
                'q': search_for
            }

            response = requests.get(search_endpoint, headers=headers, params=params)
            if response.status_code == 200 and response.json()["response"]["hits"]:
                print(artist_name)
                print(response.json()["response"]["hits"][0]["result"]["artist_names"])
                print(artist_name in response.json()["response"]["hits"][0]["result"]["artist_names"])
                if response.json()["response"]["hits"][0]["result"]["lyrics_state"] == "complete" \
                        and artist_name in response.json()["response"]["hits"][0]["result"]["artist_names"]:
                    base = "https://genius.com"
                    endpoint = response.json()["response"]["hits"][0]["result"]["path"]
                    link = base + endpoint
                    print(link)
                    header = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0"}
                    response = requests.get(url=link, headers=header)

                    contents = response.text
                    soup = BeautifulSoup(contents, "html.parser")
                    lyrics_container = soup.find_all(class_="Lyrics__Container-sc-78fb6627-1 hiRbsH")

                    text = "\n".join([block.get_text(separator="\n") for block in lyrics_container]).splitlines()
                    lyrics = "\n".join(text[2:])
                    print(lyrics)

                    return lyrics
                return ""

        def get_song_url_from_soundcloud(name):
            scraper_url = "https://spotify-scraper.p.rapidapi.com/v1/track/download/soundcloud"

            querystring = {"track": f"{name} {artist_name}", "quality": "sq"}

            headers = {
                "x-rapidapi-key": os.getenv("RAPID_API_KEY"),
                "x-rapidapi-host": "spotify-scraper.p.rapidapi.com"
            }

            scraper_data = requests.get(scraper_url, headers=headers, params=querystring).json()
            if "soundcloudTrack" in scraper_data:
                return scraper_data["soundcloudTrack"]["audio"][0]["url"]
            else:
                return "https://example.com"

        def get_track_preview_from_spotify(song_id):
            track_url = f"https://open.spotify.com/track/{song_id}"

            response = requests.get(track_url)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                og_audio_tag = soup.find('meta', property='og:audio')

                if og_audio_tag:
                    url = og_audio_tag.get('content')
                    print(url)
                    return url
                else:
                    print("Audio URL not found in the meta tags.")
                    return "https://fakeurl.com"
            else:
                print(f"Error: Unable to fetch the page. Status code: {response.status_code}")
                return "https://fakeurl.com"

        # artist_top_songs = get_top_10_tracks()
        # print(artist_top_songs)
        # for song in artist_top_songs:
        #     song_name = song["name"]
        #     spotify_id = song["id"]
        #     print(f"Adding song - {song_name}")
        #     duration = datetime.timedelta(milliseconds=song["duration_ms"])
        #     release_date = song["album"]["release_date"]
        #     if len(release_date) == 4:
        #         release_date = datetime.datetime.strptime(release_date + "-01-01", "%Y-%m-%d").date()
        #
        #     artist_objs = []
        #
        #     for artist in song["artists"]:
        #         print(artist["name"])
        #         artist_obj, _ = Artist.objects.get_or_create(
        #             spotify_id=artist["id"],
        #             defaults={"name": artist["name"]}
        #         )
        #         artist_objs.append(artist_obj)
        #
        #     lyrics = get_lyrics_from_genius(song_name)
        #     if lyrics:
        #         lang = detect(lyrics)
        #         if lang == "ru":
        #             "song_name is in russian - nonono"
        #             continue
        #     popularity = song["popularity"]
        #     audio_url = get_track_preview_from_spotify(spotify_id)
        #     album = None
        #     image_url = None
        #
        #     album_type = song["album"]["album_type"]
        #     if album_type == "single":
        #         image_url = song["album"]["images"][0]["url"]
        #     elif album_type == "album":
        #         album_id = song["album"]["id"]
        #         album = ArtistAlbum.objects.filter(spotify_id=album_id).first()
        #
        #         if not album:
        #             print("Album not found. Creating...")
        #             release_date = song["album"]["release_date"]
        #             if len(release_date) == 4:
        #                 release_date = datetime.datetime.strptime(release_date + "-01-01", "%Y-%m-%d").date()
        #
        #             album = ArtistAlbum.objects.create(
        #                 name=song["album"]["name"],
        #                 owner=self.object,
        #                 release_date=release_date,
        #                 image_url=song["album"]["images"][0]["url"],
        #                 spotify_id=album_id
        #             )
        #     song, created = Song.objects.get_or_create(
        #         spotify_id=spotify_id,
        #         defaults={
        #             "name": song_name,
        #             "album": album,
        #             "duration": duration,
        #             "release_date": release_date,
        #             "audio_url": audio_url,
        #             "lyrics": lyrics if lyrics else "",
        #             "image_url": image_url if image_url else None,
        #             "popularity": popularity,
        #         }
        #     )
        #
        #     if created:
        #         song.artists.set(artist_objs)  # use .set() to assign all at once
        #     else:
        #         song.artists.add(*artist_objs)

        # UPDATE LYRICS
        #     if not created and lyrics:
        #         # Only update lyrics if the song already exists and lyrics is provided
        #         print("Updating lyrics...")
        #         song.lyrics = lyrics
        #         song.save(update_fields=['lyrics'])

        # UPDATE AUDIO WITH PREVIEW
        # for song in self.object.songs.all():
        #     audio_url = get_track_preview_from_spotify(song.spotify_id)
        #
        #     if audio_url:
        #         song.audio_url = audio_url
        #         song.save(update_fields=['audio_url'])
        #     time.sleep(random.uniform(1, 3))

        context['songs'] = Song.objects.filter(artists=self.object)[:10]
        context['albums'] = self.object.albums.all()
        context['platform_mixes'] = self.object.get_platform_mixes()  # artist playlists
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

        if not UserPlaylistSong.objects.filter(playlist=favorites_playlist, song=song).exists():
            UserPlaylistSong.objects.create(playlist=favorites_playlist, song=song)

            # Return the filled heart SVG icon when added
            icon_svg = '''
            <svg class="heart-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="#e600ff">
                              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5
                                       2 5.42 4.42 3 7.5 3c1.74 0 3.41 0.81 4.5 2.09
                                       C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5
                                       c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                            </svg>
            '''
            return JsonResponse({'status': 'added', 'icon': icon_svg})

        else:
            # If the song is already in the playlist, return the empty heart SVG icon
            playlist_song = UserPlaylistSong.objects.filter(playlist=favorites_playlist, song=song).first()
            playlist_song.delete()
            icon_svg = '''
            <svg class="heart-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#e600ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5
                                       2 5.42 4.42 3 7.5 3c1.74 0 3.41 0.81 4.5 2.09
                                       C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5
                                       c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                            </svg>
            '''
            return JsonResponse({'status': 'already_added', 'icon': icon_svg})
