"""Build the demo database and show what the pipeline does.

    python scripts/demo.py                       # data quality report and a market lookup
    python scripts/demo.py --ask "question"      # also ask the Claude assistant (needs ANTHROPIC_API_KEY)
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from infocars.db import build_database, market_price, price_position  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ask", help="Question for the pricing assistant")
    args = parser.parse_args()

    conn, report = build_database(ROOT / "data" / "sample_listings.csv")

    print("Data quality")
    print(f"  raw listings:                {report['raw']}")
    print(f"  dropped for bad price:       {report['bad_price']}")
    print(f"  dropped as price outliers:   {report['outliers']}")
    print(f"  dropped, no full match:      {report['incomplete']}")
    print(f"  matched to the catalogue:    {report['matched']} ({report['fuzzy']} through typo correction)")
    print(f"  make/model spellings in ads: {report['raw_model_spellings']} -> {report['canonical_models']} models")

    print("\nMarket for a 2023 Chevrolet Onix LTZ, all states")
    for key, value in market_price(conn, "onix", "ltz", 2023).items():
        print(f"  {key}: {value}")

    print("\nA dealer asking R$ 89,900 for the same car")
    result = price_position(conn, "onix", "ltz", 2023, 89_900)
    print(f"  {result.get('position')}, {result.get('gap_to_median_brl')} BRL from the median")

    if args.ask:
        from infocars.assistant import ask
        print(f"\nQ: {args.ask}\nA: {ask(args.ask, conn)}")


if __name__ == "__main__":
    main()
