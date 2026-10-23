import pytest

from infocars.normalize import clean, extract_year, match_listing


@pytest.mark.parametrize(
    "title, expected",
    [
        ("Chevrolet Onix 1.0 LTZ 2023", ("chevrolet", "onix", "ltz", 2023)),
        ("GM ONIX LT 1.0 FLEX MANUAL 22/23", ("chevrolet", "onix", "lt", 2023)),
        ("onix premier 2024", ("chevrolet", "onix", "premier", 2024)),
        ("VW Polo Highline 1.0 Turbo 2022", ("volkswagen", "polo", "highline", 2022)),
        ("Hyundai HB-20 Platinum Aut. 2021", ("hyundai", "hb20", "platinum", 2021)),
        ("Jeep Compass Limited 2020", ("jeep", "compass", "limited", 2020)),
    ],
)
def test_exact_matches(title, expected):
    m = match_listing(title)
    assert (m.make, m.model, m.version, m.year) == expected
    assert m.method == "exact"


@pytest.mark.parametrize(
    "title, expected",
    [
        ("Toyota Corola XEi 2021", ("toyota", "corolla", "xei", 2021)),
        ("HB20 Platinun 2023", ("hyundai", "hb20", "platinum", 2023)),
        ("Jeep Compas Longitud 2022", ("jeep", "compass", "longitude", 2022)),
        ("Onix Premiere 2024", ("chevrolet", "onix", "premier", 2024)),
    ],
)
def test_typos_are_corrected(title, expected):
    m = match_listing(title)
    assert (m.make, m.model, m.version, m.year) == expected
    assert m.method == "fuzzy"


def test_lt_is_not_confused_with_ltz():
    assert match_listing("Onix LTZ 2023").version == "ltz"
    assert match_listing("Onix LT 2023").version == "lt"


def test_unknown_car_is_unmatched():
    m = match_listing("Ford Ka SE 2019")
    assert m.method == "unmatched"
    assert not m.is_complete


def test_missing_version_is_incomplete():
    m = match_listing("Fiat Argo 1.0 2022")
    assert m.model == "argo"
    assert m.version is None
    assert not m.is_complete


def test_clean_removes_accents_and_punctuation():
    assert clean("Automático, ÚNICO dono!") == "automatico unico dono"


@pytest.mark.parametrize("text, year", [("onix 22/23", 2023), ("onix 1.0 2021", 2021), ("onix 1.0", None)])
def test_extract_year(text, year):
    assert extract_year(text) == year
