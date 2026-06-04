import time
import logging
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ..constants import MISSING_AUDIO_URL

logger = logging.getLogger(__name__)


def build_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--log-level=3")

    return webdriver.Chrome(options=options)


class SpotifyScraper:
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver

    @staticmethod
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

    def scrape_playlist(self, playlist_id: str) -> dict:
        """
        Returns:
        {
            "id": str,
            "title": str | None,
            "image_url": str | None,
            "tracks": [
                {
                    "id": str,
                    "name": str,
                    "artist": {
                        "id": str | None,
                        "name": str | None,
                    },
                    "album": {
                        "id": str | None,
                    },
                    "duration_ms": int,
                    "release_date": str,
                    "popularity": int,
                }
            ]
        }
        """

        url = f"https://open.spotify.com/playlist/{playlist_id}"
        self.driver.get(url)

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'a[href^="/track/"]')
            )
        )

        time.sleep(2)  # allow JS render

        soup = BeautifulSoup(self.driver.page_source, "html.parser")

        title = soup.select_one("h1")
        playlist_title = title.get_text(strip=True) if title else None

        img = soup.find("img", {"data-testid": "card-image"})
        image_url = img["src"] if img else None

        tracks = self._extract_tracks(soup)

        logger.info(
            "Scraped playlist %s with %s tracks",
            playlist_id,
            len(tracks),
        )

        return {
            "id": playlist_id,
            "title": playlist_title,
            "image_url": image_url,
            "tracks": tracks,
        }

    @staticmethod
    def _extract_tracks(soup: BeautifulSoup) -> list[dict]:
        tracks = []

        track_links = soup.select('a[href^="/track/"]')

        logger.info("Tracks to extract: %s", len(tracks))

        for track_link in track_links:
            href = track_link.get("href", "")
            track_id = href.split("/")[-1]
            if not track_id:
                continue

            track_container = track_link.find_parent("div")

            artist_link = track_container.find_next("a", href=lambda x: x and "/artist/" in x)
            album_link = track_container.find_next("a", href=lambda x: x and "/album/" in x)
            artist_id = artist_link["href"].split("/")[-1] if artist_link else None
            artist_name = artist_link.get_text(strip=True) if artist_link else None
            album_id = album_link['href'].split('/')[-1] if album_link else None

            track_data = {
                "id": track_id,
                "name": track_link.get_text(strip=True),
                "artist": {
                    "id": artist_id,
                    "name": artist_name,
                },
                "album": {
                    "id": album_id,
                },
            }

            tracks.append(track_data)

        logger.info("Extracted %s tracks", len(tracks))

        return tracks

