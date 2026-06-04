import requests
from bs4 import BeautifulSoup


class BillboardScraper:
    @staticmethod
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

