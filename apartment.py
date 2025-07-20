import requests
from bs4 import BeautifulSoup
import re
import json
import os
import time


#HGSSDD3WAA67E79XZ9GR18UC recovery code from twilio


TOKEN = '7713729222:AAHSjLh0ULRPMaYcHfWyvdIROhkcR097TsE'
CHAT_ID = 7747874542


DATA_FILE = "previous_listings.json"

URL = "https://rent2day.nl/wp/wp-admin/admin-ajax.php"


# This is your POST data, as seen in DevTools
PAYLOAD = {
    'action': 'jet_smart_filters',
    'provider': 'jet-engine/default',
    'defaults[post_status][]': 'publish',
    'defaults[post_type]': 'property',
    'defaults[posts_per_page]': '4',
    'defaults[paged]': '1',
    'defaults[ignore_sticky_posts]': '1',
    'settings[lisitng_id]': '530702',
    'settings[columns]': '4',
    'settings[columns_mobile]': '1',
    'settings[column_min_width]': '240',
    'settings[inline_columns_css]': 'false',
    'settings[post_status][]': 'publish',
    'settings[posts_num]': '4',
    'settings[max_posts_num]': '9',
    'settings[not_found_message]': 'No data was found',
    'settings[equal_columns_height]': 'yes',
    'settings[load_more_type]': 'click',
    'settings[load_more_offset][unit]': 'px',
    'settings[load_more_offset][size]': '0',
    'settings[carousel_enabled]': 'yes',
    'settings[slides_to_scroll]': '3',
    'settings[arrows]': 'true',
    'settings[arrow_icon]': 'fa fa-angle-left',
    'settings[autoplay]': 'true',
    'settings[pause_on_hover]': 'true',
    'settings[autoplay_speed]': '5000',
    'settings[infinite]': 'true',
    'settings[effect]': 'slide',
    'settings[speed]': '500',
    'settings[list_items_wrapper_tag]': 'div',
    'settings[list_item_tag]': 'div',
    'settings[empty_items_wrapper_tag]': 'div',
    'props[found_posts]': '27',
    'props[max_num_pages]': '5',
    'props[page]': '1'
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://rent2day.nl/',
    'Origin': 'https://rent2day.nl'
}


STATUS_KEYWORDS  = ["For Rent", "Rented Out", "Fully Booked"]

def fetch_listings():
    response = requests.post(URL, data=PAYLOAD, headers=HEADERS)
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return []

    data = response.json()
    soup = BeautifulSoup(data['content'], 'html.parser')
    items = soup.find_all(class_='jet-listing-grid__item')

    results = []
    for item in items:
        # Name
        name = 'N/A'
        heading_widgets = item.find_all("div", class_=lambda c: c and "elementor-widget-heading" in c)
        for hw in heading_widgets:
            a_tag = hw.find("a")
            if a_tag and a_tag.get_text(strip=True):
                name = a_tag.get_text(strip=True)
                break

        # Status
        status = 'Unknown'
        name_clean = name
        for keyword in STATUS_KEYWORDS:
            if keyword.lower() in name.lower():
                status = keyword
                name_clean = name.replace(keyword, '').strip(' |')
                break

        # Price
        price = 'N/A'
        text_editors = item.find_all("div", class_="elementor-widget-text-editor")
        for editor in text_editors:
            text = editor.get_text(strip=True)
            if re.match(r'^\d+$', text):
                price = text
                break

        results.append({"name": name_clean, "status": status, "price": price})

    return results


def save_listings(listings, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(listings, f, ensure_ascii=False, indent=2)

def load_listings(filename):
    if not os.path.exists(filename):
        return []
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)
    
def listings_changed(old, new):
    return old != new

def send_telegram_message(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    response = requests.post(url, data=payload)
    return response.json()



while True:
    print("\n🔄 Checking for listing updates...")
    current_listings = fetch_listings()

    previous_listings = load_listings(DATA_FILE)

    if listings_changed(previous_listings, current_listings):
        print("✅ Listings changed!")
        message = "🚨 The rental listings have changed!\n"
        for item in current_listings:
            message += f"- {item['name']} | €{item['price']}\n"

        sent = send_telegram_message(TOKEN, CHAT_ID, message)
        if sent:
            print("✅ Telegram message sent!")
        else:
            print("❌ Failed to send Telegram message.")

        save_listings(current_listings, DATA_FILE)
    else:
        print("✅ No change detected.")

    print("⏳ Sleeping for 1 hour...\n")
    time.sleep(60 * 60)

