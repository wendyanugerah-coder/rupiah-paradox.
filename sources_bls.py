"""Retrieve monthly U.S. CPI from the official BLS API or bulk data file."""

import io

import pandas as pd


def _monthly_index(rows, spec, start, end, delivery):
    table = pd.DataFrame(rows, columns=["year", "period", "value"])
    table = table.loc[table["period"].ne("M13")]
    if table.empty:
        raise ValueError("BLS returned no monthly CPI rows.")
    dates = pd.to_datetime(table["year"].astype(str) + "-" + table["period"], format="%Y-M%m", errors="raise")
    values = pd.to_numeric(table["value"].str.strip().replace("-", float("nan")), errors="raise")
    series = pd.Series(values.to_numpy(), index=pd.DatetimeIndex(dates), dtype=float).sort_index().loc[start:end]
    series.attrs.update(delivery=delivery, retrieval_url=spec["url"], retrieval_series_id=spec["id"])
    return series


def retrieve_bls_api(session, spec, start, end):
    """Read BLS Public Data API v2 in inclusive ten-calendar-year batches."""
    series_id = spec["id"]
    rows = []
    for last_year in range(end.year, start.year - 1, -10):
        first_year = max(start.year, last_year - 9)
        response = session.post(spec["url"], json={
            "seriesid": [series_id],
            "startyear": str(first_year),
            "endyear": str(last_year),
        })
        response.raise_for_status()
        payload = response.json()
        if payload.get("status") != "REQUEST_SUCCEEDED" or payload.get("message"):
            raise ValueError(f"BLS did not return the requested {first_year}–{last_year} CPI batch.")
        returned = payload["Results"]["series"]
        if len(returned) != 1 or returned[0]["seriesID"] != series_id or not returned[0]["data"]:
            raise ValueError(f"BLS returned unexpected series data for {first_year}–{last_year}.")
        for observation in returned[0]["data"]:
            year = int(observation["year"])
            if not first_year <= year <= last_year:
                raise ValueError("BLS observation falls outside its requested calendar years.")
            rows.append((year, observation["period"], observation["value"]))
    return _monthly_index(rows, spec, start, end, "BLS Public Data API v2")


def retrieve_bls_bulk(session, spec, start, end):
    """Read the identical series ID from the BLS CPI-U all-items data file."""
    response = session.get(spec["url"])
    response.raise_for_status()
    table = pd.read_csv(io.BytesIO(response.content), sep="\t", dtype=str)
    table.columns = table.columns.str.strip()
    rows = table.loc[table["series_id"].str.strip().eq(spec["id"]), ["year", "period", "value"]]
    return _monthly_index(rows, spec, start, end, "BLS CPI-U all-items bulk file")
