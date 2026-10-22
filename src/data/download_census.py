"""Download Census ACS 5-year estimates for the geographies in config/geography.yml.

Outputs
-------
data/raw/census/acs5_<geography>_<year>.json   Untouched API responses (one per geography-year)
data/interim/acs5_tidy.csv                     Combined, numeric, long-by-year table
data/provenance/downloads.jsonl                One log line per raw file

Usage
-----
    python -m chicago_forecast.data.download_census
    python -m chicago_forecast.data.download_census --years 2019 2022 --geographies cook_county
    python -m chicago_forecast.data.download_census --force      # re-download existing files

Requires CENSUS_API_KEY in .env (free: https://api.census.gov/data/key_signup.html).
The API also works without a key at a low rate limit, so a missing key only warns.

Notes
-----
* Variable codes occasionally change between ACS vintages. If a year fails with an HTTP error,
  check https://api.census.gov/data/<year>/acs/acs5/variables.html
* ACS 5-year values are overlapping 5-year averages, NOT independent annual observations.
  Do not treat consecutive years as independent data points in regressions.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from chicago_forecast.utils.provenance import load_config, log_download, repo_root

log = logging.getLogger(__name__)

API_URL = "https://api.census.gov/data/{year}/acs/acs5"

# The Census API encodes missing/suppressed estimates as large negative sentinels
# (e.g. -666666666, -999999999, -222222222). They must never reach an analysis.
SENTINEL_THRESHOLD = -111111111


def make_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=4,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def build_params(variables: list[str], geo: dict, api_key: str | None) -> dict:
    params = {"get": ",".join(["NAME", *variables]), "for": geo["for"]}
    if geo.get("in"):
        params["in"] = geo["in"]
    if api_key:
        params["key"] = api_key
    return params


def fetch_acs(session: requests.Session, year: int, params: dict) -> list[list[str]]:
    """Return the raw JSON table (first row = header). Raises on HTTP errors."""
    resp = session.get(API_URL.format(year=year), params=params, timeout=60)
    resp.raise_for_status()
    return resp.json()


def clean_table(raw: list[list[str]], year: int, geography: str, rename: dict[str, str]) -> pd.DataFrame:
    """Raw API rows -> numeric DataFrame with sentinels replaced by NA."""
    df = pd.DataFrame(raw[1:], columns=raw[0])
    value_cols = [c for c in df.columns if c in rename]
    for col in value_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df.loc[df[col] <= SENTINEL_THRESHOLD, col] = pd.NA
    df = df.rename(columns=rename)
    df.insert(0, "geography", geography)
    df.insert(1, "acs5_end_year", year)
    return df


def run(years: list[int], geography_names: list[str], force: bool = False) -> pd.DataFrame:
    load_dotenv(repo_root() / ".env")
    api_key = os.getenv("CENSUS_API_KEY")
    if not api_key:
        log.warning("CENSUS_API_KEY not set; using the keyless (rate-limited) API.")

    geos = load_config("geography")["geographies"]
    cfg = load_config("data_sources")["census_acs5"]
    rename: dict[str, str] = cfg["variables"]
    variables = list(rename)

    unknown = [g for g in geography_names if g not in geos]
    if unknown:
        raise SystemExit(f"Unknown geographies {unknown}. Available: {list(geos)}")

    raw_dir = repo_root() / "data" / "raw" / "census"
    interim_dir = repo_root() / "data" / "interim"
    raw_dir.mkdir(parents=True, exist_ok=True)
    interim_dir.mkdir(parents=True, exist_ok=True)

    session = make_session()
    tables: list[pd.DataFrame] = []

    for geo_name in geography_names:
        for year in years:
            out_path = raw_dir / f"acs5_{geo_name}_{year}.json"
            params = build_params(variables, geos[geo_name], api_key)

            if out_path.exists() and not force:
                log.info("Skipping %s (exists; use --force to re-download)", out_path.name)
                raw = json.loads(out_path.read_text())
            else:
                try:
                    raw = fetch_acs(session, year, params)
                except requests.HTTPError as err:
                    log.warning("FAILED %s %s: %s", geo_name, year, err)
                    continue
                out_path.write_text(json.dumps(raw))
                safe_params = {k: v for k, v in params.items() if k != "key"}  # never log the key
                log_download(
                    source="US Census Bureau ACS 5-year API",
                    url=API_URL.format(year=year),
                    params=safe_params,
                    out_path=out_path,
                )
                log.info("Downloaded %s", out_path.name)
                time.sleep(0.2)  # be polite

            tables.append(clean_table(raw, year, geo_name, rename))

    if not tables:
        raise SystemExit("No data retrieved; see warnings above.")

    tidy = pd.concat(tables, ignore_index=True)
    tidy.to_csv(interim_dir / "acs5_tidy.csv", index=False)
    log.info("Wrote %d rows to data/interim/acs5_tidy.csv", len(tidy))
    return tidy


def main() -> None:
    cfg = load_config("data_sources")["census_acs5"]
    geos = load_config("geography")["geographies"]

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--years", type=int, nargs="+", default=cfg["years"])
    parser.add_argument("--geographies", nargs="+", default=list(geos))
    parser.add_argument("--force", action="store_true", help="re-download files that already exist")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run(args.years, args.geographies, force=args.force)


if __name__ == "__main__":
    main()
