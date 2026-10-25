"""Write the catalogue and the title matches as dbt seeds.

Matching free-text titles needs the Python matcher (exact aliases on whole words, then fuzzy
matching for typos), so it is not rewritten in SQL. This script runs the repository's own
matcher (infocars/normalize.py) over data/sample_listings.csv and writes:

    seeds/listing_matches.csv    one row per raw ad: make, model, version, model year, method
    seeds/catalog_versions.csv   canonical versions with display names and body type

Run it from the dashboards folder: python scripts/match_titles.py
"""
import csv
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
REPO = HERE.parent
sys.path.insert(0, str(REPO))

from infocars.catalog import CATALOG  # noqa: E402
from infocars.normalize import match_listing  # noqa: E402

RAW = Path(os.environ.get("INFOCARS_RAW_PATH", REPO / "data")) / "sample_listings.csv"

# Display names as the generator writes them; body type of each model.
MAKE_NAMES = {"chevrolet": "Chevrolet", "hyundai": "Hyundai", "fiat": "Fiat", "volkswagen": "Volkswagen",
              "toyota": "Toyota", "jeep": "Jeep"}
MODEL_NAMES = {"onix": ("Onix", "Hatch"), "tracker": ("Tracker", "SUV"), "hb20": ("HB20", "Hatch"),
               "argo": ("Argo", "Hatch"), "polo": ("Polo", "Hatch"), "corolla": ("Corolla", "Sedan"),
               "compass": ("Compass", "SUV")}
VERSION_NAMES = {"ls": "LS", "lt": "LT", "ltz": "LTZ", "premier": "Premier", "sense": "Sense", "comfort": "Comfort",
                 "vision": "Vision", "platinum": "Platinum", "drive": "Drive", "trekking": "Trekking", "mpi": "MPI",
                 "comfortline": "Comfortline", "highline": "Highline", "gts": "GTS", "gli": "GLi", "xei": "XEi",
                 "altis": "Altis", "sport": "Sport", "longitude": "Longitude", "limited": "Limited"}


def main():
    with open(RAW, newline="", encoding="utf-8") as f, \
         open(HERE / "seeds" / "listing_matches.csv", "w", newline="", encoding="utf-8") as out:
        w = csv.writer(out)
        w.writerow(["listing_id", "make", "model", "version", "model_year", "match_method", "title_spelling"])
        n = 0
        for row in csv.DictReader(f):
            m = match_listing(row["title"])
            # first two words of the title: how the seller wrote make and model (same rule as infocars/db.py)
            spelling = " ".join(row["title"].lower().split()[:2])
            w.writerow([row["id"], m.make or "", m.model or "", m.version or "", m.year or "", m.method, spelling])
            n += 1

    with open(HERE / "seeds" / "catalog_versions.csv", "w", newline="", encoding="utf-8") as out:
        w = csv.writer(out)
        w.writerow(["version_key", "make", "model", "version", "make_name", "model_name", "version_name", "body_type", "sort_order"])
        i = 0
        for make, mspec in CATALOG.items():
            for model, spec in mspec["models"].items():
                for version in spec["versions"]:
                    i += 1
                    name, body = MODEL_NAMES[model]
                    w.writerow([f"{model}|{version}", make, model, version, MAKE_NAMES[make], name,
                                VERSION_NAMES[version], body, i])
    print(f"{n} titles matched, {i} catalogue versions written to seeds/")


if __name__ == "__main__":
    main()
