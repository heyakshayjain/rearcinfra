
"""Minimal BLS → S3 true sync.

What it does:

    - Reads the BLS directory listing (no hardcoded filenames).
    - Uploads/updates objects in S3 under a prefix.
    - Deletes S3 objects under that prefix that are not on BLS.

Example:
	python3 data/ingestion/ingest.py --bucket my-bucket --prefix raw/bls/
"""

from __future__ import annotations
import re
import urllib.request


# Central config.
from data.constants import BLS_BASE_URL, S3_BUCKET, S3_PREFIX  # type: ignore

DEFAULT_HEADERS = {

    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}


def list_bls_manifest(base_url: str, timeout_seconds: int = 30) -> dict[str, tuple[str, int]]:
	"""Read BLS directory listing and return: filename -> (timestamp, size_bytes)."""

	req = urllib.request.Request(
		base_url,
		headers=DEFAULT_HEADERS,
		method="GET",
	)
	with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
		html = resp.read().decode("utf-8", errors="replace")

	# Normalize <br> to newlines and fix occasional "<\n" line-breaks.
	html_norm = html.replace("<\n", "<").replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")

	manifest: dict[str, tuple[str, int]] = {}
	line_re = re.compile(
		r"^\s*(\d{1,2}/\d{1,2}/\d{4})\s+"
		r"(\d{1,2}:\d{2})\s+(AM|PM)\s+"
		r"(\d+)\s+<A\s+HREF=\"[^\"]+\">([^<]+)</A>",
		re.IGNORECASE,
	)
	for line in html_norm.splitlines():
		m = line_re.search(line)
		if not m:
			continue
		mmddyyyy, hhmm, ampm, size_str, name = m.groups()
		filename = name.strip()
		if not re.fullmatch(r"[A-Za-z0-9._-]+", filename):
			continue
		# Keep the timestamp in the same human format as the listing.
		source_ts = f"{mmddyyyy} {hhmm} {ampm.upper()}"
		manifest[filename] = (source_ts, int(size_str))

	if not manifest:
		raise RuntimeError("Could not parse BLS directory listing")
	return manifest



def _download_bls_file(base_url: str, filename: str, timeout_seconds: int = 60) -> bytes:
	"""Download one BLS file."""

	url = base_url.rstrip("/") + "/" + filename.lstrip("/")
	req = urllib.request.Request(
		url,
		headers={**DEFAULT_HEADERS, "Accept": "*/*"},
		method="GET",
	)
	with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
		return resp.read()


def sync_bls_to_s3(
	*,
	base_url: str,
	bucket: str,
	prefix: str,
	timeout_seconds: int = 60,
) -> None:
	"""True sync: upload/update from BLS and delete extra S3 keys."""

	import boto3  # type: ignore

	s3 = boto3.client("s3")
	prefix = prefix.strip().strip("/")
	key_prefix = (prefix + "/") if prefix else ""

	# 1) Source manifest
	source_manifest = list_bls_manifest(base_url, timeout_seconds=timeout_seconds)
	if not source_manifest:
		return
	source_set = set(source_manifest.keys())

	# 2) Destination listing (for delete step)
	s3_names: set[str] = set()
	paginator = s3.get_paginator("list_objects_v2")
	for page in paginator.paginate(Bucket=bucket, Prefix=key_prefix):
		for obj in page.get("Contents", []) or []:
			key = obj.get("Key") or ""
			if not key.startswith(key_prefix):
				continue
			name = key[len(key_prefix) :]
			if name:
				s3_names.add(name)

	print(f"CHECKPOINT source({len(source_set)}): {sorted(source_set)} | destination({len(s3_names)}): {sorted(s3_names)}")

	uploaded = 0
	deleted = 0
	for filename, (source_ts, source_size) in source_manifest.items():
		key = key_prefix + filename

		body = _download_bls_file(base_url, filename, timeout_seconds=timeout_seconds)
		metadata = {
			"bls_timestamp": source_ts,
			"bls_size": str(source_size),
		}

		s3.put_object(Bucket=bucket, Key=key, Body=body, Metadata=metadata)
		uploaded += 1

	# 3) True sync delete
	to_delete: list[dict[str, str]] = [{"Key": key_prefix + name} for name in (s3_names - source_set)]

	if to_delete:
		# S3 DeleteObjects accepts up to 1000 keys per request.
		for i in range(0, len(to_delete), 1000):
			chunk = to_delete[i : i + 1000]
			s3.delete_objects(Bucket=bucket, Delete={"Objects": chunk, "Quiet": True})
		deleted = len(to_delete)

	print(f"Synced {len(source_manifest)} files: uploaded={uploaded}, deleted={deleted}")


def main() -> int:
	"""Program entrypoint."""

	base_url = BLS_BASE_URL
	bucket = S3_BUCKET
	prefix = S3_PREFIX

	sync_bls_to_s3(
		base_url=base_url,
		bucket=bucket,
		prefix=prefix,
	)
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
