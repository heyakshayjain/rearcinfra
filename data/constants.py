
"""Shared configuration constants for the data code.

This repo's `data/` code is treated as standalone, so we hardcode the
destination bucket/prefix here.
"""

from __future__ import annotations

import os


BLS_BASE_URL: str = "https://download.bls.gov/pub/time.series/pr/"

# Hardcoded destination for sync.
S3_BUCKET: str = os.getenv("S3_BUCKET", "akshays3-2026")
S3_PREFIX: str = os.getenv("S3_PREFIX", "raw/bls")


DATAUSA_API_URL: str = (
    "https://honolulu-api.datausa.io/tesseract/data.jsonrecords"
    "?cube=acs_yg_total_population_1"
    "&drilldowns=Year%2CNation"
    "&locale=en"
    "&measures=Population"
)

DATAUSA_S3_KEY: str = "raw/datausa/population.json"
