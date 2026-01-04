"""AWS Lambda entrypoint for Part 1 + Part 2 ingestion.

This wraps the existing local modules so they can be deployed as a zip-based
Lambda without rewriting the ingestion logic.
"""

from __future__ import annotations


def handler(event, context):  # noqa: ANN001

    from data.ingestion.ingest import main as bls_main
    from data.ingestion.usapi import main as datausa_main

    bls_main()
    datausa_main()
    return {"ok": True}
