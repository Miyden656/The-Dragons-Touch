from pathlib import Path
import json

SCRYFALL_FILE = Path("data/scryfall_cards.json")

if not SCRYFALL_FILE.exists():
    print("Could not find data/scryfall_cards.json")
    exit()

print("Loading Scryfall card data...")

cards = json.loads(SCRYFALL_FILE.read_text(encoding="utf-8"))

print(f"Loaded {len(cards)} Scryfall card records.")

card_lookup = {}

for card in cards:
    name = card.get("name")

    if name:
        card_lookup[name.lower()] = card

test_cards = [
    "Sol Ring",
    "Witherbloom, the Balancer",
    "Gravecrawler",
    "Craterhoof Behemoth",
]

print()
print("Testing card lookups")
print("-" * 30)

for card_name in test_cards:
    card = card_lookup.get(card_name.lower())

    if card:
        print(f"Found: {card['name']}")
        print(f"Type: {card.get('type_line', 'Unknown')}")
        print(f"Mana Value: {card.get('cmc', 'Unknown')}")
        print()
    else:
        print(f"Not found: {card_name}")
