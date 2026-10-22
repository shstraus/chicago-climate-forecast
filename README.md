# chicago-climate-forecast
## Overview
One paragraph: research question, geography, horizon, and the core contribution
(conventional growth baseline + climate damages from CMIP6-driven projections).

## Research Questions
1. ...
2. ...

## Method Summary
Baseline projection → climate projection → damage functions → adjusted forecast
(include a simple diagram)

## Data Sources
| Dataset | Provider | Geography | Years | Script |
(table linking each source to the script that downloads it)

## Repository Structure
chicago-climate-forecast/
├── README.md
├── LICENSE
├── CITATION.cff
├── pyproject.toml            # or environment.yml (conda is easier for xarray/netCDF/geo stack)
├── .gitignore
├── .env.example              # API key names only, never real keys
├── Makefile                  # or Snakemake; one command runs the pipeline
│
├── config/
│   ├── geography.yml         # FIPS codes, bounding box, station IDs
│   ├── scenarios.yml         # SSPs, models, time horizons
│   └── data_sources.yml      # URLs, versions, access dates
│
├── data/                     # mostly gitignored, see section 4
│   ├── raw/                  # untouched downloads (never edited by hand)
│   ├── interim/              # cleaned, intermediate
│   ├── processed/            # analysis-ready (small ones may be committed)
│   └── README.md             # data dictionary and provenance
│
├── src/chicago_forecast/
│   ├── data/                 # download_census.py, download_bea.py, download_cmip6.py
│   ├── climate/              # downscaling, bias correction, degree-day / bin construction
│   ├── baseline/             # conventional growth projection
│   ├── damages/              # damage functions, one module per sector
│   ├── forecast/             # combine baseline + damages, scenarios, uncertainty
│   └── utils/
│
├── notebooks/                # exploration only; numbered (01_explore_acs.ipynb)
├── tests/                    # unit tests for unit conversions, merges, etc.
├── docs/                     # methodology notes, literature log, decision log
├── results/
│   ├── figures/
│   └── tables/
└── references/               # .bib file (PDFs usually stay out of git)

## Setup
- Environment creation (conda/pip) commands
- API keys needed (Census, BEA, FRED...) and where to put them (.env)

## Reproducing the Analysis
Ordered commands (e.g., `make data`, `make climate`, `make forecast`)

## Scenarios and Assumptions
SSPs used, models used, discount rate, base period, key limitations

## Limitations
Be upfront: downscaling uncertainty, damage-function transferability,
no adaptation modeling, etc.

## Citation / License / Contact
