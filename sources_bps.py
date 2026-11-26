"""Link Statistics Indonesia's national CPI using its published monthly changes."""

import calendar
import json
import re

import pandas as pd
from lxml import html


def parse_bps_monthly_changes(source):
    """Read the year-by-month table from HTML or BPS's embedded page payload."""
    document = html.fromstring(source)
    documents = [document]
    for script in document.xpath("//script/text()"):
        match = re.fullmatch(r"self\.__next_f\.push\((.*)\)", script.strip(), re.S)
        if match is None:
            continue
        payload = json.loads(match[1])
        if len(payload) > 1 and isinstance(payload[1], str) and "<table" in payload[1]:
            documents.append(html.fromstring(payload[1]))

    for page in documents:
        for table in page.xpath("//table"):
            rows = [
                [" ".join(cell.text_content().split()) for cell in row.xpath("./td|./th")]
                for row in table.xpath(".//tr")
            ]
            if rows and "National Consumer Price Inflation Rate (M-to-M)" in " ".join(rows[0]):
                return _monthly_changes(rows)
    raise ValueError("BPS national monthly CPI inflation table was not found")


def _monthly_changes(rows):
    years = next(
        (row[1:] for row in rows if row and row[0] == "Month"),
        [],
    )
    if not years or not all(re.fullmatch(r"\d{4}", year) for year in years):
        raise ValueError("BPS CPI table has invalid year headings")
    if len(set(years)) != len(years):
        raise ValueError("BPS CPI table repeats a year")

    months = {month: i for i, month in enumerate(calendar.month_name) if month}
    changes = {}
    seen = set()
    for row in rows:
        if not row or row[0] not in months:
            continue
        month = months[row[0]]
        if month in seen or len(row) != len(years) + 1:
            raise ValueError(f"BPS CPI table has an invalid {row[0]} row")
        seen.add(month)
        for year, value in zip(years, row[1:], strict=True):
            if value in ("", "-", "–", "—", "NA", "N/A"):
                continue
            changes[pd.Timestamp(int(year), month, 1)] = float(value.replace(",", "."))
    if len(seen) != 12 or not changes:
        raise ValueError("BPS CPI table is missing calendar rows or observations")
    return pd.Series(changes, dtype=float).sort_index()


def retrieve_id_cpi(session, spec, start, end):
    """Chain published CPI growth factors from the configured index anchor."""
    response = session.get(
        spec["url"], headers={"User-Agent": "Mozilla/5.0"}, timeout=(10, 30)
    )
    response.raise_for_status()
    rates = parse_bps_monthly_changes(response.content)
    anchor = pd.Timestamp(spec["anchor_month"])
    if start.to_period("M").to_timestamp() < anchor:
        raise ValueError("Requested BPS CPI history begins before the anchor month")
    if anchor not in rates:
        raise ValueError("BPS CPI table no longer covers the configured anchor month")

    last = min(rates.index[-1], end.to_period("M").to_timestamp())
    rate_months = rates.reindex(pd.date_range(anchor, last, freq="MS"))
    if rate_months.isna().any():
        missing = rate_months[rate_months.isna()].index.strftime("%Y-%m").tolist()
        raise ValueError(f"BPS CPI linking requires the missing monthly rates: {missing}")
    gross_growth = 1.0 + rate_months / 100.0
    if not gross_growth.between(0.5, 1.5).all():
        raise ValueError("BPS CPI monthly growth is outside the validation range")
    gross_growth.loc[anchor] = 1.0
    levels = float(spec["anchor_value"]) * gross_growth.cumprod()
    return levels.loc[start:end]
