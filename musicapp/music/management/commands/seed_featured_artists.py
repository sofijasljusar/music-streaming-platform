import os
import requests
import logging

from django.core.management import BaseCommand

from ...constants import FEATURED_ARTIST_IDS
from ...models import Artist

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Populate featured artists from official Spotify API'

    def handle(self, *args, **kwargs):
        names = []

        url = "https://spotify-scraper3.p.rapidapi.com/api/artists/info"
        headers = {
            "x-rapidapi-key": os.getenv("RAPID_API_KEY"),
            "x-rapidapi-host": "spotify-scraper3.p.rapidapi.com"
        }

        for artist_id in FEATURED_ARTIST_IDS:
            try:
                response = requests.get(url, headers=headers, params={"id": artist_id}, timeout=10)

                response.raise_for_status()

                data = response.json()["data"]["artist"]
                name = data["name"]
                avatar_img = data["avatar_images"][0]["url"]
                header_img = data["header_images"][0]["url"]
                names.append(name)

                artist, created = Artist.objects.get_or_create(
                    spotify_id=artist_id,
                    defaults={
                        "name": name,
                        "profile_image": avatar_img,
                        "detail_image": header_img,
                    }
                )

                if created:
                    logger.info("Created artist: %s", name)
                else:
                    logger.info("Created artist: %s", name)

            except requests.RequestException as e:
                logger.error("Request failed for %s: %s", artist_id, e)

        logger.info("Loaded artists: %s", names)
