from pathlib import Path
import json
import urllib.request

DATA_FOLDER = Path("data")
SCRYFALL_BULK_DATA_URL = "https://api.scryfall.com/bulk-data"
OUTPUT_FILE = DATA_FOLDER / "scryfall_cards.json"

HEADERS = {
    "User-Agent": "MTG-Deck-Helper/0.2 (personal project by Bruce)",
    "Accept": "application/json;q=0.9,*/*;q=0.8",
}


def download_json(url):
    request = urllib.request.Request(url, headers=HEADERS)

    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def download_file(url, output_path):
    request = urllib.request.Request(url, headers=HEADERS)

    with urllib.request.urlopen(request) as response:
        data = response.read()

    output_path.write_bytes(data)


DATA_FOLDER.mkdir(exist_ok=True)

print("Checking Scryfall bulk data...")

bulk_data = download_json(SCRYFALL_BULK_DATA_URL)

default_cards = None

for item in bulk_data["data"]:
    if item["type"] == "default_cards":
        default_cards = item
        break

if default_cards is None:
    print("Could not find Scryfall default_cards bulk data.")
    exit()

download_uri = default_cards["download_uri"]

print("Found Scryfall default_cards file.")
print("Downloading card data...")
print("This may take a little while.")

download_file(download_uri, OUTPUT_FILE)

print(f"Saved Scryfall data to {OUTPUT_FILE}")
