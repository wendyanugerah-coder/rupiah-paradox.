"""Relative PPP and real exchange rate accounting for monthly data."""

import math

import numpy as np
import pandas as pd


BASE_YEARS = (2015, 2017, 2019, 2021)


def calculate(frame, metadata, base_year=2015):
    """Return chart series and the latest complete common-month decomposition."""
    base = pd.Timestamp(year=int(base_year), month=1, day=1)
    data = frame.copy().sort_index()
    if base not in data.index:
        raise ValueError(f"Base month {base:%Y-%m} is outside the snapshot.")
    prices = ["idr", "cpi_id", "cpi_us"]
    currencies = ["idr", "myr", "thb", "php"]
    required = list(dict.fromkeys(prices + currencies))
    levels = data.loc[base, required]
    if levels.isna().any() or (levels <= 0).any():
        raise ValueError(f"Base month {base:%Y-%m} has missing or invalid levels.")

    data["inflation_id"] = 100 * (data["cpi_id"] / data["cpi_id"].shift(12) - 1)
    data["inflation_us"] = 100 * (data["cpi_us"] / data["cpi_us"].shift(12) - 1)
    relative_prices = (data["cpi_id"] / levels["cpi_id"]) / (data["cpi_us"] / levels["cpi_us"])
    data["ppp_idr"] = levels["idr"] * relative_prices
    data["actual_index"] = 100 * (data["idr"] / levels["idr"])
    data["ppp_index"] = 100 * relative_prices
    data["q"] = data["idr"] * data["cpi_us"] / data["cpi_id"]
    data["real_index"] = 100 * (data["q"] / data.at[base, "q"])
    for name in currencies:
        data[f"{name}_index"] = 100 * (data[name] / levels[name])
    data["policy_us"] = (data["policy_us_lower"] + data["policy_us_upper"]) / 2
    data["interest_diff"] = data["policy_id"] - data["policy_us"]

    incomplete = {
        pd.Timestamp(month)
        for key in prices
        for month in metadata["series"][key].get("incomplete_months", [])
    }
    complete = data.loc[base:, prices].dropna().index.difference(pd.DatetimeIndex(sorted(incomplete)))
    if base not in complete or complete.empty:
        raise ValueError(f"Base month {base:%Y-%m} must have complete FX and CPI observations.")
    latest = complete.max()
    nominal = 100 * math.log(data.at[latest, "idr"] / levels["idr"])
    inflation = 100 * math.log(relative_prices.at[latest])
    real = nominal - inflation
    if not np.isclose(real, 100 * math.log(data.at[latest, "q"] / data.at[base, "q"]), atol=1e-10):
        raise ValueError("Real exchange rate and log decomposition disagree.")
    return data.loc[base:], {
        "base_month": base,
        "latest_month": latest,
        "nominal": nominal,
        "inflation": inflation,
        "real": real,
        "inflation_share": 100 * inflation / nominal if nominal != 0 else None,
    }
