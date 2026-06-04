import os
import requests

from ..constants import MISSING_AUDIO_URL


class SoundcloudService:
    @staticmethod
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
