"""Generate the synthetic listings in data/sample_listings.csv.

None of this is real data. Titles are written with the same kinds of mess found
in real ads (missing make, abbreviations, typos, "22/23" years, extra words) so
the matcher has something to work on. A fixed seed keeps the file reproducible.
"""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)
OUT = Path(__file__).resolve().parent.parent / "data" / "sample_listings.csv"

# make, make spellings, model, model spellings, {version: base price for the newest year (BRL)}
CARS = [
    ("Chevrolet", ["Chevrolet", "CHEVROLET", "GM", "Chevy", ""], "Onix", ["Onix", "ONIX", "onix"],
     {"LS": 72000, "LT": 80000, "LTZ": 88000, "Premier": 98000}),
    ("Chevrolet", ["Chevrolet", "GM", ""], "Tracker", ["Tracker", "TRACKER", "Traker"],
     {"LT": 118000, "LTZ": 130000, "Premier": 142000}),
    ("Hyundai", ["Hyundai", "HYUNDAI", ""], "HB20", ["HB20", "HB 20", "hb20", "HB-20"],
     {"Sense": 70000, "Comfort": 78000, "Vision": 84000, "Platinum": 96000}),
    ("Fiat", ["Fiat", "FIAT", ""], "Argo", ["Argo", "ARGO"], {"Drive": 79000, "Trekking": 92000}),
    ("Volkswagen", ["Volkswagen", "VW", "Volks", ""], "Polo", ["Polo", "POLO"],
     {"MPI": 82000, "Comfortline": 95000, "Highline": 108000, "GTS": 130000}),
    ("Toyota", ["Toyota", "TOYOTA", ""], "Corolla", ["Corolla", "COROLLA", "Corola"],
     {"GLi": 140000, "XEi": 155000, "Altis": 175000}),
    ("Jeep", ["Jeep", "JEEP", ""], "Compass", ["Compass", "COMPASS", "Compas"],
     {"Sport": 150000, "Longitude": 168000, "Limited": 190000}),
]
TYPOS = {"Platinum": "Platinun", "Longitude": "Longitud", "Highline": "Highlin", "Premier": "Premiere"}
EXTRAS = ["1.0", "1.0 Flex", "1.0 Turbo", "Flex", "Manual", "Automático", "Aut.", "Completo", "Único dono", ""]
STATES = ["SP"] * 5 + ["MG"] * 2 + ["RJ"] * 2 + ["PR", "RS", "SC", "GO", "BA"]
SOURCES = ["portal_a", "portal_b", "portal_c"]
NEWEST_YEAR = 2025


def title_for(make_spellings, model_spellings, version, year):
    make = random.choice(make_spellings)
    model = random.choice(model_spellings)
    shown_version = TYPOS[version] if version in TYPOS and random.random() < 0.15 else version
    if random.random() < 0.3:
        shown_version = shown_version.upper()
    year_text = f"{str(year - 1)[2:]}/{str(year)[2:]}" if random.random() < 0.3 else str(year)
    parts = [make, model, random.choice(EXTRAS), shown_version, year_text]
    if random.random() < 0.3:
        parts[2], parts[3] = parts[3], parts[2]
    return " ".join(p for p in parts if p)


def main():
    rows = []
    for i in range(1, 1201):
        make, make_sp, model, model_sp, versions = random.choice(CARS)
        version = random.choice(list(versions))
        year = random.choice(range(NEWEST_YEAR - 6, NEWEST_YEAR + 1))
        age = NEWEST_YEAR - year
        price_factor = random.uniform(0.9, 1.1)  # how far this ad sits from the "true" market price
        price = versions[version] * (0.89 ** age) * price_factor
        km = int(max(0, age * random.uniform(9000, 16000) + random.uniform(-3000, 3000)))

        # A few broken prices, as in real ads: missing, or typed without the last digit.
        if random.random() < 0.02:
            price_text = ""
        elif random.random() < 0.02:
            price_text = f"{price / 10:.0f}"
        else:
            price_text = f"{round(price, -2):.0f}"

        listed = date(2025, 5, 1) + timedelta(days=random.randint(0, 170))
        # Cars priced below market leave the site faster: 22 days on average at -10%, 68 days at +10%.
        mean_days = 45 * (1 + (price_factor - 1) * 5)
        days_online = int(random.expovariate(1 / mean_days))
        removed = listed + timedelta(days=days_online)
        removed_text = removed.isoformat() if removed <= date(2025, 11, 1) else ""

        rows.append({
            "id": i,
            "source": random.choice(SOURCES),
            "title": title_for(make_sp, model_sp, version, year),
            "price_brl": price_text,
            "km": km,
            "state": random.choice(STATES),
            "listed_at": listed.isoformat(),
            "removed_at": removed_text,
        })

    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} synthetic listings to {OUT}")


if __name__ == "__main__":
    main()
