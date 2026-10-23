"""Match free-text car ads to the canonical catalogue.

Ads are written by people, so the same car shows up as "Onix 1.0 LT",
"CHEVROLET ONIX LT 1.0 FLEX MANUAL" or "onix lt 22/23". The matcher works in
three steps:

1. Clean the text (lowercase, no accents, no punctuation).
2. Find make, model and version by exact alias match on tokens.
3. If a model or version is still missing, try a fuzzy match on the remaining
   tokens to catch typos such as "corola" or "platinun".
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from difflib import get_close_matches

from .catalog import CATALOG

MIN_YEAR, MAX_YEAR = 2000, 2027
FUZZY_CUTOFF = 0.8
FUZZY_MIN_LEN = 4  # short tokens like "lt" are never fuzzy-matched


@dataclass(frozen=True)
class Match:
    make: str | None
    model: str | None
    version: str | None
    year: int | None
    method: str  # "exact", "fuzzy" or "unmatched"

    @property
    def is_complete(self) -> bool:
        return all([self.make, self.model, self.version, self.year])


def clean(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = text.lower()
    text = re.sub(r"[^a-z0-9/. ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_year(text: str) -> int | None:
    # "22/23" means manufactured in 2022, model year 2023. Prices follow the model year.
    pair = re.search(r"\b(\d{2})/(\d{2})\b", text)
    if pair:
        return 2000 + int(pair.group(2))
    for token in re.findall(r"\b(\d{4})\b", text):
        if MIN_YEAR <= int(token) <= MAX_YEAR:
            return int(token)
    return None


def _find_alias(text: str, aliases: list[str]) -> bool:
    return any(re.search(rf"\b{re.escape(alias)}\b", text) for alias in aliases)


def _fuzzy(tokens: list[str], aliases: dict[str, list[str]]) -> str | None:
    lookup = {alias: name for name, names in aliases.items() for alias in names if len(alias) >= FUZZY_MIN_LEN}
    for token in tokens:
        if len(token) < FUZZY_MIN_LEN:
            continue
        hit = get_close_matches(token, lookup.keys(), n=1, cutoff=FUZZY_CUTOFF)
        if hit:
            return lookup[hit[0]]
    return None


def match_listing(title: str) -> Match:
    text = clean(title)
    tokens = text.split()
    year = extract_year(text)
    method = "exact"

    make = next((m for m, spec in CATALOG.items() if _find_alias(text, spec["aliases"])), None)

    # Search models of the detected make, or of every make when the ad omits it ("Onix LT 2022").
    makes = [make] if make else list(CATALOG)
    model = None
    for candidate_make in makes:
        for name, spec in CATALOG[candidate_make]["models"].items():
            if _find_alias(text, spec["aliases"]):
                make, model = candidate_make, name
                break
        if model:
            break

    if not model:
        all_models = {
            (m, name): spec["aliases"] for m in makes for name, spec in CATALOG[m]["models"].items()
        }
        hit = _fuzzy(tokens, {key: aliases for key, aliases in all_models.items()})
        if hit:
            make, model = hit
            method = "fuzzy"

    version = None
    if model:
        versions = CATALOG[make]["models"][model]["versions"]
        version = next((v for v, aliases in versions.items() if _find_alias(text, aliases)), None)
        if not version:
            version = _fuzzy(tokens, versions)
            if version:
                method = "fuzzy"

    if not (make or model):
        method = "unmatched"
    return Match(make, model, version, year, method)
