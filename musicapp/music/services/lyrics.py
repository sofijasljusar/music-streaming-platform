import os
import requests
from bs4 import BeautifulSoup

from langdetect import detect
from googletrans import Translator

TRANSLATION_EXCEPTIONS = {
    "Забий": "Let It Go",
    "ДІВ ЧИНА": "Girl",
    "Вишнi": "Cherries",
    "27": "27",
}


class LyricsService:
    @staticmethod
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

    @staticmethod
    def is_blocked_language(lyrics):
        return detect(lyrics) == "ru"