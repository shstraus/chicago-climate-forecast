import json

import pandas as pd

from chicago_forecast.data import download_census as dc

RAW = [
    ["NAME", "B01003_001E", "B19013_001E", "state", "county"],
    ["Cook County, Illinois", "5150233", "-666666666", "17", "031"],
]
RENAME = {"B01003_001E": "total_population", "B19013_001E": "median_household_income"}


def test_clean_table_renames_and_masks_sentinels():
    df = dc.clean_table(RAW, 2022, "cook_county", RENAME)
    assert df.loc[0, "total_population"] == 5150233
    assert pd.isna(df.loc[0, "median_household_income"])
    assert df.loc[0, "acs5_end_year"] == 2022
    assert df.loc[0, "geography"] == "cook_county"


def test_build_params_omits_missing_in_clause_and_key():
    p = dc.build_params(["B01003_001E"], {"for": "county:031", "in": None}, None)
    assert "in" not in p and "key" not in p
    assert p["get"] == "NAME,B01003_001E"
