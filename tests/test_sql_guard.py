import pytest

from infocars.sql_guard import SqlGuardError, check_sql


def test_select_gets_a_limit():
    assert check_sql("SELECT * FROM listings").endswith("LIMIT 200")


def test_existing_limit_is_kept():
    assert check_sql("SELECT * FROM listings LIMIT 5;") == "SELECT * FROM listings LIMIT 5"


def test_cte_names_are_allowed():
    sql = "WITH cheap AS (SELECT * FROM listings WHERE price_brl < 80000) SELECT model, COUNT(*) FROM cheap GROUP BY model"
    assert check_sql(sql)


@pytest.mark.parametrize(
    "sql, reason",
    [
        ("DELETE FROM listings", "Only SELECT"),
        ("SELECT * FROM listings; DROP TABLE listings", "one statement"),
        ("SELECT * FROM raw_listings", "not allowed: raw_listings"),
        ("SELECT * FROM listings l JOIN sqlite_master s ON 1=1", "not allowed: sqlite_master"),
        ("SELECT * FROM listings -- hidden", "Comments"),
        ("WITH x AS (SELECT 1) UPDATE listings SET price_brl = 0", "write or admin"),
        ("", "Empty"),
    ],
)
def test_refused_queries(sql, reason):
    with pytest.raises(SqlGuardError, match=reason):
        check_sql(sql)
