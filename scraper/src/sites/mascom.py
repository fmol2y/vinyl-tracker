import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.mascom.rs"

def parse_price(price_str):
    """Parse Serbian price string (e.g. '44.999,00') to float."""
    price_str = price_str.replace('.', '').replace(',', '.').strip()
    try:
        return float(price_str)
    except ValueError:
        return None

def scrape_vinyls(page_url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(page_url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")

    vinyls = []

    ul = soup.find("ul", class_="items_group")
    if not ul:
        print("No vinyl list found on page.")
        return vinyls

    for li in ul.find_all("li", recursive=False):
        data_id = li.get("data-id")
        item_img_tag = li.select_one(".item_img img")
        image_url = BASE_URL + item_img_tag["src"] if item_img_tag else None

        artist_tag = li.select_one(".artist_author .item_link")
        artist = artist_tag.get_text(strip=True) if artist_tag else None

        album_tag = li.select_one(".album_book .item_link")
        album = album_tag.get_text(strip=True) if album_tag else None

        medium_tag = li.select_one(".item_medium")
        medium = medium_tag.get_text(strip=True) if medium_tag else None

        price_tag = li.select_one(".item_price")
        price = None
        if price_tag:
            price_str = price_tag.contents[0].strip()
            price = parse_price(price_str)

        detail_url_tag = li.select_one(".item_img_link")
        detail_url = BASE_URL + detail_url_tag["href"] if detail_url_tag else None

        vinyls.append({
            "id": data_id,
            "artist": artist,
            "album": album,
            "medium": medium,
            "price": price,
            "image_url": image_url,
            "detail_url": detail_url,
        })

    return vinyls

if __name__ == "__main__":
    url = "https://www.mascom.rs/sr/muzika.1.90.html?pack[]=4&sorting_list=pd&_limit=12"
    vinyls = scrape_vinyls(url)
    for v in vinyls:
        print(v)