"""Retrieve target ranges and the broad dollar index from the Federal Reserve Board."""

from datetime import datetime
from io import BytesIO
from xml.etree import ElementTree
from zipfile import ZipFile

import pandas as pd
from lxml import html


def retrieve_fed_target(session, spec, start, end):
    """Read dated target-range changes and reconstruct the daily in-force policy setting."""
    response = session.get(spec["url"], timeout=(12, 20))
    response.raise_for_status()
    document = html.fromstring(response.content)
    rows = []
    for table in document.xpath("//table"):
        headings = [" ".join(cell.text_content().split()) for cell in table.xpath("./thead/tr/th")]
        if headings != ["Date", "Increase", "Decrease", "Level (%)"]:
            continue
        year = table.xpath("string(preceding::h4[1])").strip()
        if not year.isdecimal():
            raise ValueError("Federal Reserve target-rate table has an invalid year heading")
        if int(year) < 2008:
            continue
        for row in table.xpath("./tbody/tr"):
            date_text, _, _, level = [cell.text_content().strip() for cell in row.xpath("./td")]
            bounds = level.replace("–", "-").split("-")
            if len(bounds) != 2:
                # The Board used a single target before December 2008.
                if year == "2008":
                    continue
                raise ValueError("Federal Reserve policy-rate row has no target range")
            date = datetime.strptime(f"{year} {date_text.removesuffix('*').strip()}", "%Y %B %d")
            lower, upper = map(float, bounds)
            if lower >= upper:
                raise ValueError("Federal Reserve published an invalid target range")
            rows.append((date, lower, upper))
    if not rows:
        raise ValueError("Federal Reserve page contains no target ranges")
    changes = pd.DataFrame(rows, columns=["date", "lower", "upper"]).set_index("date").sort_index()
    if changes.index.has_duplicates or changes.index[0] > start:
        raise ValueError("Federal Reserve target range is duplicated or absent at the start date")
    us_today = pd.Timestamp.now(tz="America/New_York").normalize().tz_localize(None)
    end = min(end, us_today)
    recorded = changes.loc[:end]
    bound = spec.get("bound") or {"DFEDTARL": "lower", "DFEDTARU": "upper"}[spec["id"]]
    # FOMC settings stay in force through weekends, holidays and meetings without a change.
    days = pd.date_range(start, end, freq="D", name="date")
    series = recorded[bound].reindex(days, method="ffill")
    latest_change = recorded.index[-1].date().isoformat()
    series.attrs.update(
        delivery="Federal Reserve Board published FOMC target changes",
        retrieval_url=spec["url"],
        effective_change_date=latest_change,
        native_date_method="Daily in-force target range derived from published effective dates",
    )
    return series


def retrieve_fed_dollar(session, spec, start, end):
    """Read the nominal broad daily index from the Board's official H.10 XML package."""
    response = session.get(spec["url"], timeout=(12, 20))
    response.raise_for_status()
    series_id = spec["original_id"]
    with ZipFile(BytesIO(response.content)) as archive:
        with archive.open(spec.get("xml_member", "H10_data.xml")) as source:
            series = next(
                (node for _, node in ElementTree.iterparse(source, events=("end",))
                 if node.get("SERIES_NAME") == series_id),
                None,
            )
    if series is None or series.get("FREQ") != "9" or series.get("FX") != "BRD":
        raise ValueError("Federal Reserve H.10 package has no matching daily broad dollar series")
    rows = [(node.attrib["TIME_PERIOD"], None if node.get("OBS_STATUS") == "ND" else node.attrib["OBS_VALUE"])
            for node in series if node.tag.rsplit("}", 1)[-1] == "Obs"]
    if not rows:
        raise ValueError("Federal Reserve H.10 broad dollar series has no observations")
    frame = pd.DataFrame(rows, columns=["date", "value"])
    index = pd.DatetimeIndex(pd.to_datetime(frame["date"], format="%Y-%m-%d", errors="raise"), name="date")
    values = pd.to_numeric(frame["value"], errors="raise").to_numpy()
    result = pd.Series(values, index=index).sort_index().loc[start:end]
    result.attrs.update(delivery="Federal Reserve Board H.10 XML package", retrieval_url=spec["url"])
    return result
