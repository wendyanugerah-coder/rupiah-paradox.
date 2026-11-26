"""Retrieval of Bank Indonesia's JISDOR and policy-rate observations."""

from io import StringIO
from xml.etree import ElementTree

import pandas as pd


def _daily_quotes(rows, start, end):
    frame = pd.DataFrame(rows, columns=["date", "value"])
    if frame.empty:
        raise ValueError("JISDOR returned zero observations")
    frame["date"] = pd.to_datetime(frame["date"], format="%Y-%m-%d")
    frame["value"] = pd.to_numeric(frame["value"]).astype(float)
    if frame["date"].duplicated().any() or not frame["value"].between(1, 1_000_000).all():
        raise ValueError("JISDOR data contain duplicate dates or invalid values")
    series = frame.set_index("date")["value"].sort_index().loc[start:end]
    if series.empty:
        raise ValueError("JISDOR returned no observations in the requested range")
    if start + pd.Timedelta(days=14) < series.index[0] or series.index[-1] + pd.Timedelta(days=14) < end:
        raise ValueError("JISDOR does not cover the requested range within 14 days at both endpoints")
    periods = series.index.to_period("M").unique()
    if len(periods) != len(pd.period_range(periods[0], periods[-1], freq="M")):
        raise ValueError("JISDOR data omit an entire month inside the returned date range")
    return series


def retrieve_jisdor(session, spec, start, end):
    """Read daily USD reference fixings directly from Bank Indonesia."""
    response = session.post(
        spec["url"],
        data={"mts": spec["id"], "startDate": start.date().isoformat(), "endDate": end.date().isoformat()},
        timeout=30,
    )
    response.raise_for_status()
    rows = []
    for node in ElementTree.fromstring(response.content).iter():
        if node.tag.rsplit("}", 1)[-1] != "Table":
            continue
        fields = {child.tag.rsplit("}", 1)[-1]: child.text for child in node}
        day = fields.get("tgl_subkursasing")
        sell = fields.get("jual_subkursasing")
        buy = fields.get("beli_subkursasing")
        if not day or not sell:
            raise ValueError("JISDOR ASMX observation fields were absent")
        if buy and float(buy) != float(sell):
            raise ValueError("JISDOR ASMX buy and sell values disagree")
        rows.append((day[:10], sell))
    series = _daily_quotes(rows, start, end)
    series.attrs.update(retrieval_url=spec["url"], delivery="Bank Indonesia web service")
    return series


def retrieve_bi_policy(session, spec, start, end):
    """Get BI's announced policy instrument via BIS, already measured at month-end."""
    response = session.get(
        spec["url"],
        params={"startPeriod": start.strftime("%Y-%m"), "endPeriod": end.strftime("%Y-%m"), "format": "csvfile"},
        timeout=30,
    )
    response.raise_for_status()
    frame = pd.read_csv(StringIO(response.text))
    if frame.empty or not frame["FREQ"].eq("M").all() or not frame["REF_AREA"].eq("ID").all():
        raise ValueError("BIS returned an empty series or an unexpected frequency or reference area")
    if not frame["SOURCE_REF"].eq("Bank Indonesia").all() or not frame["TITLE"].str.contains("End of period", regex=False).all():
        raise ValueError("BIS policy-rate source or monthly time reference changed")
    index = pd.to_datetime(frame["TIME_PERIOD"], format="%Y-%m")
    values = pd.to_numeric(frame["OBS_VALUE"], errors="raise").astype(float)
    series = pd.Series(values.to_numpy(), index=pd.DatetimeIndex(index, name="date")).sort_index()
    if series.index.has_duplicates:
        raise ValueError("BIS returned duplicate Bank Indonesia policy-rate months")
    series.attrs.update(retrieval_url=spec["url"], delivery="BIS distribution of Bank Indonesia policy rates")
    return series
