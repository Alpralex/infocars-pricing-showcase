"""Generate the synthetic listings in data/sample_listings.csv and the price history in data/sample_price_changes.csv.

None of this is real data. Titles are written with the same kinds of mess found
in real ads (missing make, abbreviations, typos, "22/23" years, extra words) so
the matcher has something to work on. A fixed seed keeps the file reproducible.

Version 2 (November 2026) adds the attributes the production table had (seller type, transmission, fuel,
colour, photos, city), a price history, and makes mileage depend on the price. The title, price, state, portal
and dates of every ad are the same as in version 1, drawn from the same random sequence, so every number the
quality checks and the market statistics produce is unchanged. The new columns come from a second generator
conditioned on how far each ad sits from its market price, which plants the patterns the dashboards look for:

- private sellers ask less than dealers, dealers more (seller type explains part of the gap to market);
- the fewer the kilometres, the higher the asking price for the same car and year;
- automatic gearboxes are asked for more; colour and fuel change almost nothing;
- about one ad in seven cut its price once while online, and the cut ones sold at the pace of their new price.
"""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)
OUT = Path(__file__).resolve().parent.parent / "data" / "sample_listings.csv"
OUT_CHANGES = OUT.with_name("sample_price_changes.csv")

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
SNAPSHOT = date(2025, 11, 1)

# Version 2 attributes. Only the automatic gearbox is always available on the versions listed here.
CITIES = {"SP": ["São Paulo", "Campinas", "Sorocaba", "Ribeirão Preto"], "MG": ["Belo Horizonte", "Uberlândia"],
          "RJ": ["Rio de Janeiro", "Niterói"], "PR": ["Curitiba", "Londrina"], "RS": ["Porto Alegre", "Caxias do Sul"],
          "SC": ["Florianópolis", "Joinville"], "GO": ["Goiânia"], "BA": ["Salvador"]}
COLOURS = [("White", 30), ("Silver", 20), ("Black", 20), ("Grey", 15), ("Red", 8), ("Blue", 7)]
AUTOMATIC_ONLY = {"Tracker", "Corolla", "Compass"}
MANUAL_ONLY = {"MPI", "LS", "Sense", "Drive"}


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


def weighted(rng, pairs):
    return rng.choices([p[0] for p in pairs], weights=[p[1] for p in pairs])[0]


def attributes(rng, model, version, age, price_factor, price_ok, listed, days_online, price):
    """The version 2 columns for one ad, conditioned on how far the ad sits from its market price (price_factor,
    0.9 to 1.1) so the patterns described at the top of this file hold. Returns (columns, price change or None)."""
    gap = price_factor - 1  # -0.1 (cheap) .. +0.1 (dear)
    seller = "private" if rng.random() < 0.45 - gap * 2.5 else "dealer"  # 70% private at -10%, 20% at +10%
    if model in AUTOMATIC_ONLY:
        transmission = "automatic"
    elif version in MANUAL_ONLY:
        transmission = "manual"
    else:
        transmission = "automatic" if rng.random() < 0.5 + gap * 2 else "manual"  # 30% at -10%, 70% at +10%
    fuel = "hybrid" if version == "Altis" and rng.random() < 0.5 else ("petrol" if rng.random() < 0.1 else "flex")
    colour = weighted(rng, COLOURS)
    photos = rng.randint(8, 24) if seller == "dealer" else rng.randint(3, 14)
    # Mileage: the age sets the level, the price moves it. A car asked at +10% shows about 30% fewer km than
    # one asked at -10%, which is the depreciation per kilometre the dashboards estimate.
    base_km = age * rng.uniform(9000, 16000) + rng.uniform(500, 6000)
    km = int(max(500, base_km * (1 - gap * 3) + rng.uniform(-2500, 2500)))
    change = None
    # About one ad in seven cut its price once, 5 to 40 days after listing, by 3 to 10%. The current price is the
    # price after the cut; the ad sold at the pace of that price, so cuts can be shown to work.
    if price_ok and price_factor < 1.03 and days_online > 6 and rng.random() < 0.18:
        cut = rng.choice([0.03, 0.05, 0.05, 0.07, 0.10])
        day = rng.randint(5, min(40, days_online - 1))
        old_price = round(price / (1 - cut), -2)
        change = {"changed_at": (listed + timedelta(days=day)).isoformat(), "old_price_brl": f"{old_price:.0f}",
                  "new_price_brl": f"{round(price, -2):.0f}"}
    return {"km": km, "seller_type": seller, "transmission": transmission, "fuel": fuel, "colour": colour,
            "photos": photos}, change


def main():
    rows, changes = [], []
    v2 = random.Random(2026)  # the version 2 columns: a second generator, so the version 1 columns stay the same
    for i in range(1, 1201):
        make, make_sp, model, model_sp, versions = random.choice(CARS)
        version = random.choice(list(versions))
        year = random.choice(range(NEWEST_YEAR - 6, NEWEST_YEAR + 1))
        age = NEWEST_YEAR - year
        price_factor = random.uniform(0.9, 1.1)  # how far this ad sits from the "true" market price
        price = versions[version] * (0.89 ** age) * price_factor
        random.uniform(9000, 16000); random.uniform(-3000, 3000)  # version 1 mileage draws, kept for the sequence

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
        removed_text = removed.isoformat() if removed <= SNAPSHOT else ""

        row = {
            "id": i,
            "source": random.choice(SOURCES),
            "title": title_for(make_sp, model_sp, version, year),
            "price_brl": price_text,
            "km": None,
            "state": random.choice(STATES),
            "listed_at": listed.isoformat(),
            "removed_at": removed_text,
        }
        online_days = days_online if removed_text else (SNAPSHOT - listed).days
        extra, change = attributes(v2, model, version, age, price_factor, price_text == f"{round(price, -2):.0f}",
                                   listed, online_days, price)
        row.update(extra)
        row["city"] = v2.choice(CITIES[row["state"]])
        rows.append(row)
        if change:
            changes.append({"listing_id": i, **change})

    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with open(OUT_CHANGES, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["listing_id", "changed_at", "old_price_brl", "new_price_brl"])
        writer.writeheader()
        writer.writerows(changes)
    print(f"Wrote {len(rows)} synthetic listings to {OUT} and {len(changes)} price changes to {OUT_CHANGES}")


if __name__ == "__main__":
    main()
