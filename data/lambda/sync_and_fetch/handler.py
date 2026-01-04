from __future__ import annotations

from data.ingestion.lambda_handler import handler as _ingestion_handler


def lambda_handler(event, context):  # noqa: ANN001
    return _ingestion_handler(event, context)
