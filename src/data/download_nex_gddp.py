"""SKELETON: subset NASA NEX-GDDP-CMIP6 (daily, ~25 km, bias-corrected) to the Chicago region.

STATUS: untested template. The bucket layout and file naming below are NOT verified, and
they differ across models (grid label, ensemble member, version suffix). Run with --list
first and confirm the real paths before writing the download step.

Data is on AWS open data (anonymous access). Docs: search "NEX-GDDP-CMIP6" on nasa.gov /
the AWS Open Data registry. Subset at read time so you never download global fields.

Usage
-----
    python -m chicago_forecast.data.download_nex_gddp --list
    python -m chicago_forecast.data.download_nex_gddp --list --prefix nex-gddp-cmip6/NEX-GDDP-CMIP6
"""

from __future__ import annotations

import argparse
import logging

from chicago_forecast.utils.provenance import load_config, repo_root

log = logging.getLogger(__name__)

BUCKET = "nex-gddp-cmip6"  # TODO: confirm bucket name against the AWS Open Data registry


def list_bucket(prefix: str | None = None, max_items: int = 50) -> None:
    """Print what is in the bucket so you can discover models, scenarios and file names."""
    import s3fs

    fs = s3fs.S3FileSystem(anon=True)
    path = prefix or BUCKET
    for i, item in enumerate(fs.ls(path)):
        print(item)
        if i + 1 >= max_items:
            print(f"... (truncated at {max_items})")
            break


def open_and_subset(s3_path: str, bbox: dict):
    """Open one NetCDF from S3 lazily and subset to the Chicago bounding box.

    NEX-GDDP longitudes are (I believe) 0-360, while config uses -180..180. This function
    handles both, but verify against a real file.
    """
    import s3fs
    import xarray as xr

    fs = s3fs.S3FileSystem(anon=True)
    ds = xr.open_dataset(fs.open(s3_path), engine="h5netcdf", chunks={})

    lon_min, lon_max = bbox["lon_min"], bbox["lon_max"]
    if float(ds["lon"].max()) > 180:  # convert to 0-360 convention
        lon_min, lon_max = lon_min % 360, lon_max % 360

    return ds.sel(
        lat=slice(bbox["lat_min"], bbox["lat_max"]),
        lon=slice(lon_min, lon_max),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--list", action="store_true", help="list bucket contents and exit")
    parser.add_argument("--prefix", default=None, help="S3 prefix to list")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if args.list:
        list_bucket(args.prefix)
        return

    bbox = load_config("geography")["climate_bbox"]
    cfg = load_config("data_sources")["nex_gddp_cmip6"]
    out_dir = repo_root() / "data" / "raw" / "nex_gddp"
    out_dir.mkdir(parents=True, exist_ok=True)

    # TODO (after --list):
    #   1. Fill `models` in config/data_sources.yml (only models that have every scenario/variable).
    #   2. Build the S3 path for each (model, scenario, variable, year).
    #   3. ds = open_and_subset(path, bbox); ds.to_netcdf(out_dir / <name>.nc)
    #   4. Call log_download(...) for each file written (see download_census.py).
    #   5. Consider writing one Zarr store per model/scenario instead of many small .nc files.
    raise NotImplementedError(f"Finish the TODOs. Scenarios={cfg['scenarios']}, bbox={bbox}")


if __name__ == "__main__":
    main()
