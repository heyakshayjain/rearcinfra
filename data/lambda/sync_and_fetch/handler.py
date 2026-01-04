from __future__ import annotations

import os
import re
import urllib.request
from dataclasses import dataclass
from typing import Any

import boto3


BLS_BASE_URL = "https://download.bls.gov/pub/time.series/pr/"
BLS_S3_PREFIX = "raw/bls"

DATAUSA_API_URL = (
    "https://honolulu-api.datausa.io/tesseract/data.jsonrecords"
    "?cube=acs_yg_total_population_1"
    "&drilldowns=Year%2CNation"
    "&locale=en"
    "&measures=Population"
)
DATAUSA_S3_KEY = "raw/datausa/population.json"


@dataclass(frozen=True)
class BlsFile:
    name: str
    size: int


_BLS_ROW_RE = re.compile(
    r"<a\s+href=\"(?P<href>[^\"]+)\"[^>]*>[^<]+</a>\s+"
    r"(?P<ts>\d{2}-[A-Za-z]{3}-\d{4}\s+\d{2}:\d{2})\s+"
    r"(?P<size>\d+)\s*",
    re.IGNORECASE,
)


def _http_get(url: str) -> bytes:
    user_agent = os.getenv(
        "BLS_USER_AGENT",
        "rearc-data-quest (contact: you@example.com)",
    )
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def _list_bls_files() -> list[BlsFile]:
    html = _http_get(BLS_BASE_URL).decode("utf-8", errors="replace")
    files: list[BlsFile] = []

    for m in _BLS_ROW_RE.finditer(html):
        href = m.group("href")
        name = href.rsplit("/", 1)[-1]
        if not name or name.endswith("/"):
            continue
        files.append(BlsFile(name=name, size=int(m.group("size"))))

    return files


def _s3_list_sizes(bucket: str, prefix: str) -> dict[str, int]:
    client = boto3.client("s3")
    paginator = client.get_paginator("list_objects_v2")

    sizes: dict[str, int] = {}
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix.rstrip("/") + "/"):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            name = key.rsplit("/", 1)[-1]
            sizes[name] = int(obj.get("Size", 0))

    return sizes


def _s3_delete_extras(bucket: str, prefix: str, keep_names: set[str]) -> int:
    client = boto3.client("s3")
    paginator = client.get_paginator("list_objects_v2")

    to_delete: list[dict[str, str]] = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix.rstrip("/") + "/"):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            name = key.rsplit("/", 1)[-1]
            if name and name not in keep_names:
                to_delete.append({"Key": key})

    deleted = 0
    for i in range(0, len(to_delete), 1000):
        chunk = to_delete[i : i + 1000]
        if not chunk:
            continue
        client.delete_objects(Bucket=bucket, Delete={"Objects": chunk})
        deleted += len(chunk)

    return deleted


def _sync_bls_to_s3(bucket: str) -> dict[str, int]:
    src_files = _list_bls_files()
    src_by_name = {f.name: f for f in src_files}

    dst_sizes = _s3_list_sizes(bucket, BLS_S3_PREFIX)

    uploaded = 0
    s3 = boto3.client("s3")

    for name, meta in src_by_name.items():
        if dst_sizes.get(name) == meta.size:
            continue
        body = _http_get(BLS_BASE_URL + name)
        s3.put_object(Bucket=bucket, Key=f"{BLS_S3_PREFIX}/{name}", Body=body)
        uploaded += 1

    deleted = _s3_delete_extras(bucket, BLS_S3_PREFIX, set(src_by_name.keys()))

    return {"uploaded": uploaded, "deleted": deleted, "source": len(src_by_name), "dest": len(dst_sizes)}


def _fetch_datausa_to_s3(bucket: str) -> None:
    body = _http_get(DATAUSA_API_URL)
    boto3.client("s3").put_object(
        Bucket=bucket,
        Key=DATAUSA_S3_KEY,
        Body=body,
        ContentType="application/json",
    )


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    bucket = os.environ["S3_BUCKET"]

    bls = _sync_bls_to_s3(bucket)
    _fetch_datausa_to_s3(bucket)

    print(f"BLS sync: source={bls['source']} dest={bls['dest']} uploaded={bls['uploaded']} deleted={bls['deleted']}")
    print(f"Wrote population JSON: s3://{bucket}/{DATAUSA_S3_KEY}")

    return {"ok": True, "bucket": bucket, "bls": bls, "population_key": DATAUSA_S3_KEY}
