# Chicago Climate-Adjusted Economic Forecast
# Run `make help` to see available targets.
#
# NOTE: recipe lines MUST be indented with a real TAB character, not spaces.

PYTHON ?= python
ENV_NAME ?= chicago-climate

# Lets `python -m chicago_forecast...` work without installing the package.
export PYTHONPATH := src

.DEFAULT_GOAL := help
.PHONY: help env update-env data data-census data-climate-list test lint format clean clean-data

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-18s %s\n", $$1, $$2}'

# --- Environment -------------------------------------------------------------
env:  ## Create the conda environment from environment.yml
	conda env create -f environment.yml
	@echo "Activate with: conda activate $(ENV_NAME)"

update-env:  ## Update the existing conda environment after editing environment.yml
	conda env update -n $(ENV_NAME) -f environment.yml --prune

# --- Data --------------------------------------------------------------------
data: data-census  ## Download all raw data (add more targets here as you build them)

data-census:  ## Download Census ACS 5-year estimates (needs CENSUS_API_KEY in .env)
	$(PYTHON) -m chicago_forecast.data.download_census

data-climate-list:  ## Explore the NEX-GDDP-CMIP6 bucket layout (no download)
	$(PYTHON) -m chicago_forecast.data.download_nex_gddp --list

# --- Code quality ------------------------------------------------------------
test:  ## Run unit tests
	$(PYTHON) -m pytest -q

lint:  ## Check code style
	ruff check src tests

format:  ## Auto-format code
	ruff format src tests
	ruff check --fix src tests

# --- Cleanup -----------------------------------------------------------------
clean:  ## Remove Python caches
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache

clean-data:  ## Delete interim data (raw data is kept; delete it by hand if you must)
	find data/interim -type f ! -name .gitkeep -delete
