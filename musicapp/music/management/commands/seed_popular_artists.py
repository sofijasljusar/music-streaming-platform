import os
import requests
import base64
import logging
from bs4 import BeautifulSoup

from django.core.management import BaseCommand

from ...constants import POPULAR_ARTIST_IDS
from ...models import Artist

logger = logging.getLogger(__name__)


def get_spotify_api_token():
    client_id = os.getenv("SPOTIFY_ID")
    client_secret = os.getenv("SPOTIFY_SECRET")

    auth_str = f"{client_id}:{client_secret}"
    b64_auth = base64.b64encode(auth_str.encode()).decode()

    response = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={
            "Authorization": f"Basic {b64_auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "client_credentials"},
        timeout=10,
    )

    response.raise_for_status()
    return response.json()["access_token"]


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


def get_top_chart():
    url = "https://www.billboard.com/charts/artist-100/"
    headers = {
        "User-Agent": "Mozilla/5.0",
    }

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    titles = soup.select(".chart-results-list li h3")

    return [t.get_text(strip=True) for t in titles]


class Command(BaseCommand):
    help = 'Fetch and sync popular artists from Spotify API'

    def handle(self, *args, **kwargs):
        url = "https://spotify-scraper3.p.rapidapi.com/api/artists/info"
        headers = {
            "x-rapidapi-key": os.getenv("RAPID_API_KEY"),
            "x-rapidapi-host": "spotify-scraper3.p.rapidapi.com"
        }

        for artist_id in POPULAR_ARTIST_IDS:
            try:
                response = requests.get(url, headers=headers, params={"id": artist_id}, timeout=10)
                response.raise_for_status()

                data = response.json()["data"]["artist"]
                if data:
                    name = data["name"]
                    avatar_img = data["avatar_images"][0]["url"]
                    header_img = None
                    if data["header_images"]:
                        header_img = data["header_images"][0]["url"]
                    else:
                        logger.warning("No header image for artist: %s", name)
                    artist, created = Artist.objects.get_or_create(
                        spotify_id=artist_id,
                        defaults={
                            "profile_image": avatar_img,
                            "detail_image": header_img,
                            "name": name,
                        }
                    )

                    if created:
                        logger.info("Artist created: %s", name)
                    else:
                        logger.info("Artist already exists: %s", name)
                else:
                    logger.warning("No artist data returned for spotify id: %s", artist_id)

            except requests.RequestException as e:
                logger.error("Failed artist %s: %s", artist_id, e)