
"""Part 2: Fetch DataUSA population API and save JSON to S3."""

from __future__ import annotations

import urllib.request


from data.constants import DATAUSA_API_URL, DATAUSA_S3_KEY, S3_BUCKET  # type: ignore


def main() -> int:
	import boto3  # type: ignore

	req = urllib.request.Request(
		DATAUSA_API_URL, headers={"Accept": "application/json"}, method="GET"
	)
	with urllib.request.urlopen(req, timeout=30) as resp:
		body = resp.read()

	s3 = boto3.client("s3")
	s3.put_object(
		Bucket=S3_BUCKET, Key=DATAUSA_S3_KEY, Body=body, ContentType="application/json"
	)
	print(f"Saved DataUSA population data to s3://{S3_BUCKET}/{DATAUSA_S3_KEY}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
