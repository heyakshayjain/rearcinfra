from __future__ import annotations

import json
import os
from io import StringIO
from typing import Any

import boto3
import pandas as pd


BLS_KEY = "raw/bls/pr.data.0.Current"
POP_KEY = "raw/datausa/population.json"


def _load_bls_df(s3: Any, bucket: str) -> pd.DataFrame:
    obj = s3.get_object(Bucket=bucket, Key=BLS_KEY)
    content = obj["Body"].read().decode("utf-8")

    df = pd.read_csv(StringIO(content), sep="\t", dtype=str)
    df.columns = df.columns.str.strip()
    df = df.map(lambda x: x.strip() if isinstance(x, str) else x)

    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    return df


def _load_pop_df(s3: Any, bucket: str) -> pd.DataFrame:
    obj = s3.get_object(Bucket=bucket, Key=POP_KEY)
    content = obj["Body"].read().decode("utf-8")
    parsed = json.loads(content)

    rows = parsed["data"]
    df = pd.DataFrame(rows)
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["Population"] = pd.to_numeric(df["Population"], errors="coerce")
    return df


def _query_1(pop_df: pd.DataFrame) -> dict[str, float]:
    filtered = pop_df[(pop_df["Year"] >= 2013) & (pop_df["Year"] <= 2018)]
    return {
        "mean": float(filtered["Population"].mean()),
        "std": float(filtered["Population"].std()),
    }


def _query_2(bls_df: pd.DataFrame) -> pd.DataFrame:
    quarterly = bls_df[bls_df["period"].isin(["Q01", "Q02", "Q03", "Q04"])].copy()
    grouped = quarterly.groupby(["series_id", "year"], as_index=False)["value"].sum()
    best = grouped.loc[grouped.groupby("series_id")["value"].idxmax()].sort_values("series_id")
    return best


def _query_3(bls_df: pd.DataFrame, pop_df: pd.DataFrame) -> pd.DataFrame:
    filtered = bls_df[(bls_df["series_id"] == "PRS30006032") & (bls_df["period"] == "Q01")].copy()
    merged = filtered.merge(pop_df, left_on="year", right_on="Year", how="left")
    return merged[["series_id", "year", "period", "value", "Population"]]


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    bucket = os.environ["S3_BUCKET"]
    s3 = boto3.client("s3")

    bls_df = _load_bls_df(s3, bucket)
    pop_df = _load_pop_df(s3, bucket)

    q1 = _query_1(pop_df)
    print(f"Query1 mean_pop_2013_2018={q1['mean']:.0f} std={q1['std']:.2f}")

    best = _query_2(bls_df)
    print(f"Query2 best_year_rows={len(best)} sample={best.head(5).to_dict(orient='records')}")

    joined = _query_3(bls_df, pop_df)
    print(f"Query3 join_rows={len(joined)} sample={joined.head(10).to_dict(orient='records')}")

    return {"ok": True, "bucket": bucket, "q1": q1, "q2_rows": int(len(best)), "q3_rows": int(len(joined))}
