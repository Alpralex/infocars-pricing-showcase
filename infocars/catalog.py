"""Canonical vehicle catalogue.

Every listing is matched against this catalogue. Each make, model and version
has a canonical name plus the spellings people actually use in ads.
The production system had 641 models; this sample keeps a handful of
best-selling Brazilian cars so the matching logic is easy to follow.
"""

CATALOG = {
    "chevrolet": {
        "aliases": ["chevrolet", "chevy", "gm"],
        "models": {
            "onix": {
                "aliases": ["onix"],
                "versions": {"ls": ["ls"], "lt": ["lt"], "ltz": ["ltz"], "premier": ["premier"]},
            },
            "tracker": {
                "aliases": ["tracker"],
                "versions": {"lt": ["lt"], "ltz": ["ltz"], "premier": ["premier"]},
            },
        },
    },
    "hyundai": {
        "aliases": ["hyundai"],
        "models": {
            "hb20": {
                "aliases": ["hb20", "hb 20", "hb-20"],
                "versions": {
                    "sense": ["sense"],
                    "comfort": ["comfort"],
                    "vision": ["vision"],
                    "platinum": ["platinum"],
                },
            },
        },
    },
    "fiat": {
        "aliases": ["fiat"],
        "models": {
            "argo": {
                "aliases": ["argo"],
                "versions": {"drive": ["drive"], "trekking": ["trekking"]},
            },
        },
    },
    "volkswagen": {
        "aliases": ["volkswagen", "vw", "volks"],
        "models": {
            "polo": {
                "aliases": ["polo"],
                "versions": {
                    "mpi": ["mpi"],
                    "comfortline": ["comfortline"],
                    "highline": ["highline"],
                    "gts": ["gts"],
                },
            },
        },
    },
    "toyota": {
        "aliases": ["toyota"],
        "models": {
            "corolla": {
                "aliases": ["corolla"],
                "versions": {"gli": ["gli"], "xei": ["xei"], "altis": ["altis"]},
            },
        },
    },
    "jeep": {
        "aliases": ["jeep"],
        "models": {
            "compass": {
                "aliases": ["compass"],
                "versions": {"sport": ["sport"], "longitude": ["longitude"], "limited": ["limited"]},
            },
        },
    },
}
