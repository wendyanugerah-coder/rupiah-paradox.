"""Streamlit dashboard for Indonesia's exchange rate and relative PPP."""

from html import escape
from typing import NamedTuple
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from analysis import BASE_YEARS, calculate
from refresh import latest_failure, load_snapshot, refresh, series_status


INK = "#15293a"
MUTED = "#536777"
GRID = "#e6edf1"
TEAL = "#087d78"
BLUE = "#3866a3"
RUST = "#a55432"
VIOLET = "#795394"
LOCAL_ZONE = ZoneInfo("America/Chicago")

st.set_page_config(page_title="The Rupiah Paradox", page_icon="📈", layout="wide")
st.html("""
<style>
    [data-testid="stApp"], [data-testid="stAppViewContainer"] { position: relative; inset: auto;
        height: auto; min-height: 100vh; overflow: visible; }
    [data-testid="stAppViewContainer"] { background: #f6f8fa; color: #15293a; }
    [data-testid="stMain"] { height: auto; overflow: visible; }
    [data-testid="stHeader"] { background: transparent; }
    .block-container { max-width: 1400px; padding-top: 2.7rem; padding-bottom: 2rem; }
    .block-container h1, .block-container h2, .block-container h3 { color: #15293a; }
    .dashboard-label { color: #08706b; font-size: .79rem; font-weight: 700;
                       letter-spacing: .12em; text-transform: uppercase; }
    .dashboard-title { font-size: clamp(2.3rem, 4.8vw, 4.1rem); font-weight: 780;
                       line-height: 1.06; letter-spacing: -.052em; margin: .38rem 0 .55rem; }
    .dashboard-question { color: #42596a; font-size: 1.04rem; line-height: 1.5; max-width: 47rem; }
    .refresh-time { color: #536777; font-size: .79rem; line-height: 1.5; margin-top: .4rem; }
    .decomposition-period { color: #536777; font-size: .87rem; margin: .2rem 0 .4rem; }
    .metric { background: #fff; border: 1px solid #dce5eb; border-radius: .65rem;
              padding: .95rem 1.05rem .88rem; min-height: 6.5rem; }
    .metric-label { color: #445b6a; font-size: .86rem; font-weight: 650; }
    .metric-value { font-size: clamp(1.6rem, 3.2vw, 2.55rem); line-height: 1.24;
                    font-weight: 760; letter-spacing: -.045em; font-variant-numeric: tabular-nums; }
    .metric-unit { color: #536777; font-size: .74rem; }
    .dashboard-note { color: #455e6c; font-size: .85rem; line-height: 1.48;
                      padding: .55rem 0 .75rem; }
    [data-testid="stVerticalBlockBorderWrapper"], [data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: #dce5eb;
    }
    [class*="st-key-panel-"] { background: #fff; border-radius: .65rem; }
    .panel-title { color: #15293a; font-size: 1.18rem; line-height: 1.2;
                   font-weight: 740; letter-spacing: -.025em; margin: 0 0 .25rem; }
    .panel-units { color: #536777; font-size: .77rem; line-height: 1.35; }
    .latest-values { display: flex; flex-wrap: wrap; gap: .32rem 1.08rem;
                     margin: .1rem 0 .08rem; min-height: 1.35rem; }
    .latest-value { color: #42596a; font-size: .79rem; white-space: nowrap; }
    .latest-value strong { color: #15293a; font-weight: 720; font-variant-numeric: tabular-nums; }
    .line-dot { width: .52rem; height: .52rem; border-radius: 50%; display: inline-block;
                margin-right: .33rem; vertical-align: .02rem; }
    .panel-notes { border-top: 1px solid #e8eef2; padding-top: .56rem;
                   color: #435c6a; font-size: .82rem; line-height: 1.43; }
    .panel-notes > div { margin-bottom: .3rem; }
    .panel-notes > div:last-child { margin-bottom: 0; }
    .panel-notes a { color: #14655f; text-decoration-thickness: 1px; text-underline-offset: .15em; }
    .panel-notes strong { color: #213b4b; }
    .partial, .stale { color: #814915; font-weight: 650; }
    @media (max-width: 640px) {
        .block-container { padding-top: 2.1rem; }
        .metric { min-height: auto; }
    }
</style>
""")


class Line(NamedTuple):
    key: str
    label: str
    color: str
    sources: tuple[str, ...]
    dash: str = "solid"


def short_month(value):
    return pd.Timestamp(value).strftime("%b %Y")


def refresh_time(value):
    return pd.Timestamp(value).tz_convert(LOCAL_ZONE).strftime("%d %b %Y, %H:%M:%S %Z")


def metric(label, value, color):
    st.html(f"""
    <div class="metric">
        <div class="metric-label">{escape(label)}</div>
        <div class="metric-value" style="color:{color}">{value:+.2f}</div>
        <div class="metric-unit">log percentage points</div>
    </div>
    """)


def source_links(records, keys):
    sources = dict.fromkeys((records[key]["source"], records[key]["publication_url"]) for key in keys)
    return " · ".join(
        f'<a href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{escape(name)}</a>'
        for name, url in sources
    )


def line_partial_months(line, statuses):
    return {
        pd.Timestamp(month)
        for key in line.sources
        for month in statuses[key]["incomplete_months"]
    }


def draw_chart(data, statuses, lines, value_format, y_format, reference):
    fig = go.Figure()
    dates = data.index
    if reference is not None:
        fig.add_hline(y=reference, line_color="#a6b6c1", line_width=1, line_dash="dot")
    for line in lines:
        series = data[line.key]
        fig.add_trace(go.Scatter(
            x=dates, y=series, name=line.label, mode="lines", connectgaps=False,
            line={"color": line.color, "width": 2.25, "dash": line.dash},
            hovertemplate=f"{line.label} %{{y:{value_format}}}<extra></extra>",
        ))
        partial_dates = dates.intersection(sorted(line_partial_months(line, statuses)))
        if len(partial_dates):
            fig.add_trace(go.Scatter(
                x=partial_dates, y=series.loc[partial_dates], mode="markers", showlegend=False,
                marker={"size": 7, "color": line.color, "symbol": "circle-open", "line": {"width": 1.5}},
                hovertemplate=f"{line.label} %{{y:{value_format}}} (partial)<extra></extra>",
            ))
    tick_period = "M12" if (dates[-1] - dates[0]).days < 2557 else "M24"
    fig.update_layout(
        height=211, margin={"l": 51, "r": 9, "t": 9, "b": 29}, showlegend=False,
        font={"family": "Arial, sans-serif", "size": 11, "color": MUTED},
        paper_bgcolor="white", plot_bgcolor="white", hovermode="x unified",
        xaxis={"type": "date", "range": [dates[0] - pd.Timedelta(days=19), dates[-1] + pd.Timedelta(days=34)],
               "tick0": dates[0], "dtick": tick_period, "tickformat": "%Y", "hoverformat": "%b %Y",
               "showgrid": False, "showline": True, "linecolor": GRID, "fixedrange": True},
        yaxis={"tickformat": y_format, "gridcolor": GRID, "gridwidth": 1, "nticks": 5,
               "zeroline": False, "fixedrange": True, "automargin": True},
    )
    st.plotly_chart(fig, theme=None, width="stretch", key=f"plot-{lines[0].key}",
                    config={"displayModeBar": False, "scrollZoom": False}, on_select="ignore")


def chart(key, data, records, statuses, title, units, lines, method, why,
          *, digits=2, y_format=".1f", reference=None, currency=False):
    frequency = escape(units)
    if currency:
        frequency += " · Higher values mean local currency depreciation"
    value_format = f",.{digits}f"
    keys = list(dict.fromkeys(source for line in lines for source in line.sources))
    latest_values = []
    for line in lines:
        values = data[line.key].dropna()
        dot = f'<span class="line-dot" style="background:{line.color}"></span>'
        if values.empty:
            latest_values.append(f'<span class="latest-value">{dot}{escape(line.label)} · no observation</span>')
            continue
        latest, value = values.index[-1], values.iloc[-1]
        partial = '<span class="partial"> · Partial</span>' if latest in line_partial_months(line, statuses) else ""
        latest_values.append(
            f'<span class="latest-value">{dot}{escape(line.label)} '
            f'<strong>{value:{value_format}}</strong> · {short_month(latest)}{partial}</span>'
        )
    stale = [records[source]["source"] for source in keys if statuses[source]["stale"]]
    stale_html = f'<div class="stale">Over three months old · {escape(", ".join(dict.fromkeys(stale)))}</div>' if stale else ""
    with st.container(border=True, key=f"panel-{key}"):
        st.html(f'<h3 class="panel-title">{escape(title)}</h3><div class="panel-units">{frequency}</div>')
        st.html(f'<div class="latest-values">{"".join(latest_values)}</div>')
        draw_chart(data, statuses, lines, value_format, y_format, reference)
        st.html(f"""
        <div class="panel-notes">
            <div><strong>Source</strong> · {source_links(records, keys)}</div>
            <div><strong>Method</strong> · {escape(method)}</div>
            <div>{escape(why)}</div>
            {stale_html}
        </div>
        """)


def source_status(records, statuses):
    rows = []
    for key, record in records.items():
        status = statuses[key]
        month = record["native_frequency"] == "monthly"
        latest = short_month(record["latest_native_date"]) if month else record["latest_native_date"]
        rows.append({
            "Input": key,
            "Source": record["source"],
            "Native frequency": record["native_frequency"].title(),
            "Latest native date": latest,
            "Latest native value": record["latest_native_value"],
            "Units": record["units"],
            "Freshness": "Over three months old" if status["stale"] else "Within three months",
            "Incomplete months": ", ".join(map(short_month, status["incomplete_months"])) or "—",
            "Missing months": ", ".join(map(short_month, status["missing_months"])) or "—",
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")


def show_dashboard():
    left, right = st.columns([3, 1], gap="large", vertical_alignment="bottom")
    with left:
        st.html("""
        <div class="dashboard-label">Indonesia economic dashboard</div>
        <h1 class="dashboard-title">The Rupiah Paradox</h1>
        <div class="dashboard-question">
            How much of the rupiah’s depreciation against the U.S. dollar can inflation differentials account for?
        </div>
        """)
    with right:
        base_year = st.selectbox("Base month", BASE_YEARS, format_func=lambda year: f"January {year}")
        if st.button("Refresh official data", width="stretch"):
            with st.spinner("Retrieving and checking official data…"):
                success, message = refresh()
            if not success:
                st.warning(f"Refresh attempt did not complete. {message}")

    try:
        frame, metadata = load_snapshot()
        data, result = calculate(frame, metadata, base_year)
    except (FileNotFoundError, KeyError, ValueError) as error:
        st.error(f"A valid dashboard snapshot is unavailable. {error}")
        st.stop()

    records = metadata["series"]
    statuses = {key: series_status(record) for key, record in records.items()}
    with right:
        st.html('<div class="refresh-time">Last successful refresh · '
                f'{refresh_time(metadata["last_successful_refresh_utc"])}</div>')
    failure = latest_failure()
    if failure and pd.Timestamp(failure["timestamp_utc"]) > pd.Timestamp(metadata["last_successful_refresh_utc"]):
        st.warning(f'Latest refresh failed on {refresh_time(failure["timestamp_utc"])}. '
                   f'The dashboard continues to use the last validated snapshot. {failure["error"]}')

    base_month = short_month(result["base_month"])
    latest_month = short_month(result["latest_month"])
    st.html(f'<div class="decomposition-period">Cumulative change · {base_month} to {latest_month} '
            '· Latest complete common observation month</div>')
    cards = (
        ("Nominal depreciation", result["nominal"], INK),
        ("Inflation contribution", result["inflation"], RUST),
        ("Real depreciation", result["real"], TEAL),
    )
    for column, (label, value, color) in zip(st.columns(3), cards):
        with column:
            metric(label, value, color)
    share = result["inflation_share"]
    if share is None:
        contribution = ""
    elif share < 0:
        contribution = f"The inflation differential offset <strong>{abs(share):.1f}%</strong> of the nominal log change. "
    else:
        contribution = f"The inflation differential accounts for <strong>{share:.1f}%</strong> of the nominal log change. "
    st.html(f'<div class="dashboard-note">{contribution}This is an accounting contribution. '
            'The relative PPP benchmark alone cannot establish undervaluation.</div>')

    stale_names = [records[key]["source"] for key, status in statuses.items() if status["stale"]]
    if stale_names:
        st.warning("Sources over three months old · " + ", ".join(dict.fromkeys(stale_names)))

    row = st.columns(2, gap="medium", vertical_alignment="top")
    with row[0]:
        chart("nominal", data, records, statuses, "Nominal exchange rate", "IDR per USD · Monthly average",
              [Line("idr", "IDR/USD", TEAL, ("idr",))],
              "Arithmetic mean of published daily JISDOR fixings.",
              "The bilateral spot rate measures how many rupiah it takes to buy one U.S. dollar.",
              y_format=",.0f", currency=True)
    with row[1]:
        chart("inflation", data, records, statuses, "Consumer price inflation", "Percent year over year · Monthly",
              [Line("inflation_id", "Indonesia", TEAL, ("cpi_id",)), Line("inflation_us", "U.S.", BLUE, ("cpi_us",))],
              "100 × (CPI / CPI 12 months earlier − 1). Indonesia uses linked CPI levels. The October 2025 U.S. CPI gap also affects October 2026 year-over-year inflation.",
              "Inflation differences determine how far the relative PPP benchmark moves.", reference=0)

    row = st.columns(2, gap="medium", vertical_alignment="top")
    with row[0]:
        chart("ppp", data, records, statuses, "Actual versus relative PPP", f"Index, {base_month} = 100 · Monthly",
              [Line("actual_index", "Actual", TEAL, ("idr",)), Line("ppp_index", "PPP-implied", RUST, ("cpi_id", "cpi_us"), "dash")],
              "Actual uses the monthly JISDOR average. PPP applies the ratio of cumulative Indonesian and U.S. CPI growth factors to the base rate. Both are rebased to 100.",
              "The ratio of actual to PPP-implied rates tracks the real bilateral exchange rate relative to the base month.",
              reference=100, currency=True)
    with row[1]:
        chart("regional", data, records, statuses, "Regional currencies against USD", f"Index, {base_month} = 100 · Monthly",
              [Line("idr_index", "IDR", TEAL, ("idr",)), Line("myr_index", "MYR", BLUE, ("myr",)),
               Line("thb_index", "THB", RUST, ("thb",)), Line("php_index", "PHP", VIOLET, ("php",))],
              "Divide each monthly average local-currency-per-USD quote by its base-month value and multiply by 100.",
              "Comparing nearby currencies gives context for movements they share with the rupiah.",
              reference=100, currency=True)

    row = st.columns(2, gap="medium", vertical_alignment="top")
    with row[0]:
        chart("rates", data, records, statuses, "Policy rate differential", "Percentage points · Monthly, end of month",
              [Line("interest_diff", "Indonesia − U.S.", TEAL, ("policy_id", "policy_us_lower", "policy_us_upper"))],
              "Bank Indonesia’s policy rate minus the midpoint of the Fed’s target range. BI replaced its legacy policy rate with the 7-Day Reverse Repo Rate on August 19, 2016.",
              "The gap helps gauge carry incentives and gives context for interest parity.", reference=0)
    with row[1]:
        chart("dollar", data, records, statuses, "Broad U.S. dollar index", "Index, Jan 2006 = 100 · Monthly average",
              [Line("dollar", "Broad dollar", BLUE, ("dollar",))],
              "Arithmetic mean of daily Federal Reserve nominal broad dollar index observations.",
              "A higher index indicates a stronger dollar against its broad trade-weighted currency basket.")

    with st.expander("Data quality and calculation notes"):
        st.markdown(
            "Open markers flag incomplete months. The accounting cards use the latest complete month with "
            "JISDOR and both CPI levels. Blank months remain blank. The Bureau of Labor Statistics did not "
            "publish the October 2025 U.S. all-items CPI during the federal government shutdown."
        )
        st.markdown("June 2018 has 11 JISDOR fixings. Bank Indonesia suspended publication during the extended Eid al-Fitr closure.")
        st.markdown(
            "The inflation contribution uses the log change in the Indonesian-to-U.S. CPI ratio. "
            "Real depreciation is the nominal log change minus that contribution. "
            "The real rate `q` in the download equals IDR/USD × U.S. CPI ÷ Indonesian CPI. "
            "Its level depends on the CPI normalization. The `real_index` column expresses it relative to the selected base."
        )
        source_status(records, statuses)
        st.download_button("Download monthly data and calculations", data.to_csv(index_label="month").encode("utf-8"),
                           file_name=f"rupiah-monthly-base-{base_year}.csv", mime="text/csv")


show_dashboard()
