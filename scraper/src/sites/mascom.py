import requests
from bs4 import BeautifulSoup
import os
from supabase import create_client, Client
import logging
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")
logging.basicConfig(level=logging.INFO)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)

BASE_URL = "https://www.mascom.rs"

def parse_price(price_str):
    """Parse Serbian price string (e.g. '44.999,00') to float."""
    price_str = price_str.replace('.', '').replace(',', '.').strip()
    try:
        return float(price_str)
    except ValueError:
        return None

def scrape_vinyls():
    url = BASE_URL + "/sr/muzika.1.90.html?pack[]=4&sorting_list=pd&_limit=12"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")

    vinyls = []

    ul = soup.find("ul", class_="items_group")
    if not ul:
        print("No vinyl list found on page.")
        return vinyls

    # 1. Ensure site exists
    site_resp = supabase.table("sites").select("id").eq("base_url", BASE_URL).execute()
    if site_resp.data:
        site_id = site_resp.data[0]["id"]
    else:
        site_insert = supabase.table("sites").insert({"name": "Mascom", "base_url": BASE_URL}).execute()
        site_id = site_insert.data[0]["id"]

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

        # 2. Upsert vinyl
        vinyl_resp = supabase.table("vinyls").upsert({
            "artist": artist,
            "album": album
        }, on_conflict="artist,album").execute()
        vinyl_id = vinyl_resp.data[0]["id"]

        # 3. Upsert listing
        listing_resp = supabase.table("vinyl_listings").upsert({
            "site_id": site_id,
            "vinyl_id": vinyl_id,
            "detail_url": detail_url,
            "last_seen": datetime.now().isoformat(),
            "current_price": price,
            "image_url": image_url
        }, on_conflict="site_id,detail_url").execute()
        listing_id = listing_resp.data[0]["id"]

        # 4. Insert price
        supabase.table("vinyl_prices").insert({
            "listing_id": listing_id,
            "price": price
        }).execute()

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
    vinyls = scrape_vinyls()
    for v in vinyls:
        print(v)