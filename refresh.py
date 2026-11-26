"""Retrieve official inputs and atomically promote a validated monthly snapshot."""

import argparse
import io
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile

import numpy as np
import pandas as pd
import requests
import yaml
from filelock import FileLock, Timeout
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from analysis import BASE_YEARS, calculate


ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config.yaml"
DATA = ROOT / "data"
SNAPSHOT = DATA / "snapshot.json"
FAILURES = DATA / "refresh_failures.jsonl"
LOG = logging.getLogger("refresh")


class DataError(Exception):
    """A feed or snapshot did not meet the configured quality checks."""


def utc_now():
    return datetime.now(timezone.utc)


def json_write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def load_snapshot(path=SNAPSHOT):
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    frame = pd.DataFrame(payload["observations"]).set_index("month").astype(float)
    frame.index = pd.DatetimeIndex(pd.to_datetime(frame.index), name="month")
    return frame, payload["metadata"]


def latest_failure(path=FAILURES):
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as handle:
        entries = handle.read().splitlines()
    return json.loads(entries[-1]) if entries else None


def series_status(record, now=None):
    today = pd.Timestamp(now or utc_now()).tz_localize(None).normalize()
    latest = pd.Timestamp(record["latest_native_date"])
    if record["native_frequency"] == "monthly":
        latest += pd.offsets.MonthEnd(0)
    return {
        "stale": latest < today - pd.DateOffset(months=3),
        "incomplete_months": record["incomplete_months"],
        "missing_months": record["missing_months"],
    }


class DownloadSession(requests.Session):
    def request(self, method, url, **kwargs):
        kwargs.setdefault("timeout", (12, 45))
        return super().request(method, url, **kwargs)


def get_fred(session, spec, start, end):
    response = session.get(spec["url"], params={"id": spec["id"], "cosd": start.date(), "coed": end.date()})
    response.raise_for_status()
    csv = pd.read_csv(io.StringIO(response.text), na_values=["."])
    return pd.Series(pd.to_numeric(csv[spec["id"]], errors="raise").to_numpy(),
                     index=pd.to_datetime(csv["observation_date"], errors="raise"))


def get_imf(session, spec, start, end):
    response = session.get(spec["url"].format(series_id=spec["id"]),
                           params={"startPeriod": start.strftime("%Y-%m"), "endPeriod": end.strftime("%Y-%m")},
                           headers={"Accept": "text/csv"})
    response.raise_for_status()
    csv = pd.read_csv(io.StringIO(response.text))
    dates = pd.to_datetime(csv["TIME_PERIOD"].str.replace("-M", "-", regex=False), format="%Y-%m", errors="raise")
    return pd.Series(pd.to_numeric(csv["OBS_VALUE"], errors="raise").to_numpy(), index=dates)


def get_series(spec, start, end):
    provider = spec["provider"]
    if provider.startswith("bi_"):
        from sources_bi import retrieve_bi_policy, retrieve_jisdor

        adapter = {"bi_jisdor": retrieve_jisdor, "bi_policy": retrieve_bi_policy}[provider]
    elif provider == "bps":
        from sources_bps import retrieve_id_cpi

        adapter = retrieve_id_cpi
    else:
        adapter = {"fred": get_fred, "imf": get_imf}[provider]
    with DownloadSession() as session:
        session.headers["User-Agent"] = "RupiahResearchDashboard/1.0 (public economic data)"
        # The JISDOR POST is a read-only query and can safely be retried.
        session.mount("https://", HTTPAdapter(max_retries=Retry(
            total=2, backoff_factor=0.6, status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"] if provider == "bi_jisdor" else ["GET"],
            raise_on_status=False,
        )))
        return adapter(session, spec, start, end)


def monthlyize(key, native, spec, start, end):
    if not isinstance(native.index, pd.DatetimeIndex) or native.index.hasnans:
        raise DataError(f"{key}: invalid date index")
    if native.index.has_duplicates or native.index.tz is not None:
        raise DataError(f"{key}: duplicated dates or unexpected timezone")
    native = native.sort_index().loc[start:end].astype(float)
    valid = native.dropna()
    if valid.empty or not np.isfinite(valid).all():
        raise DataError(f"{key}: empty feed or invalid numeric observation")
    if spec.get("positive", True) and (valid <= 0).any():
        raise DataError(f"{key}: nonpositive observation in a positive-level series")
    if spec.get("bounds") and not valid.between(*spec["bounds"]).all():
        raise DataError(f"{key}: observation outside configured validation bounds")

    frequency = spec["frequency"]
    aggregation = spec["aggregation"]
    counts = valid.resample("MS").size()
    if frequency == "monthly" and ((counts > 1).any() or not valid.index.is_month_start.all()):
        raise DataError(f"{key}: unexpected dates or multiple observations in a native monthly series")
    if frequency == "daily" and counts.loc[counts > 0].median() < 12:
        raise DataError(f"{key}: observed frequency is inconsistent with daily data")
    if aggregation == "mean":
        monthly = valid.resample("MS").mean()
    elif aggregation in {"last", "none"}:
        monthly = valid.resample("MS").last()
    else:
        raise DataError(f"{key}: unsupported monthly aggregation")

    first_required = pd.Timestamp(spec.get("first_required", "2015-01-01"))
    current_month = end.to_period("M").to_timestamp()
    if first_required not in monthly.index or pd.isna(monthly.at[first_required]):
        raise DataError(f"{key}: no observation in required first month {first_required:%Y-%m}")
    last = valid.index.max()
    incomplete = set()
    if current_month in monthly.dropna().index:
        incomplete.add(current_month)
    if frequency == "daily":
        min_count = int(spec.get("minimum_days", 12))
        overrides = spec.get("minimum_days_overrides", {})
        limits = pd.Series([overrides.get(month.strftime("%Y-%m"), min_count) for month in counts.index], index=counts.index)
        incomplete.update(counts[(counts > 0) & (counts < limits)].index)
        last_month = last.to_period("M").to_timestamp()
        if last_month < current_month and len(pd.bdate_range(last + pd.Timedelta(days=1), last + pd.offsets.MonthEnd(0))) > 2:
            incomplete.add(last_month)

    missing = list(monthly.loc[first_required:].loc[lambda value: value.isna()].index)
    announced = set(map(pd.Timestamp, spec.get("known_missing_months", [])))
    record = {
        "source": spec["source"],
        "publication_url": spec["source_url"],
        "source_id": spec.get("id"),
        "official_id": spec.get("original_id", spec.get("id")),
        "retrieval_url": spec["url"].format(series_id=spec["id"]),
        "native_frequency": frequency,
        "units": spec["units"],
        "aggregation": aggregation,
        "first_native_date": valid.index.min().date().isoformat(),
        "latest_native_date": last.date().isoformat(),
        "latest_native_value": float(valid.iloc[-1]),
        "native_observations": len(valid),
        "latest_month_native_observations": int(counts.iloc[-1]),
        "monthly_observations": int(monthly.count()),
        "incomplete_months": [month.date().isoformat() for month in sorted(incomplete)],
        "missing_months": [month.date().isoformat() for month in missing],
        "unexplained_missing_months": [month.date().isoformat() for month in missing if month not in announced],
        **native.attrs,
    }
    LOG.info("%s | %s %s via %s | %s to %s | %s native values | %s monthly values | latest %.10g | stale=%s | incomplete=%s | missing=%s",
             key, spec.get("id", ""), frequency, record.get("delivery", spec["provider"]),
             record["first_native_date"], record["latest_native_date"],
             len(valid), record["monthly_observations"], record["latest_native_value"],
             series_status(record, end)["stale"], record["incomplete_months"], record["missing_months"])
    if record["unexplained_missing_months"]:
        raise DataError(f"{key}: unexplained missing monthly observations {record['unexplained_missing_months']}")
    return monthly, record


def safe_error(error):
    if isinstance(error, requests.HTTPError):
        code = error.response.status_code if error.response is not None else "unknown"
        return f"HTTP {code}"
    if isinstance(error, (DataError, ValueError, OSError)) and not isinstance(error, requests.RequestException):
        return f"{type(error).__name__}: {error}"
    return type(error).__name__


def collect(config, start, end):
    specs = config["series"]
    results, records, errors = {}, {}, {}
    with ThreadPoolExecutor(max_workers=6) as pool:
        pending = {key: pool.submit(get_series, spec, start, end) for key, spec in specs.items()}
        for key, task in pending.items():
            try:
                results[key], records[key] = monthlyize(key, task.result(), specs[key], start, end)
            except Exception as error:
                errors[key] = safe_error(error)
                LOG.error("%s | %s", key, errors[key])
    if errors:
        raise DataError("; ".join(f"{key} {message}" for key, message in errors.items()))
    month_index = pd.date_range(start.to_period("M").to_timestamp(), end.to_period("M").to_timestamp(), freq="MS", name="month")
    return pd.DataFrame(results).reindex(month_index), records


def refresh(config_path=CONFIG, snapshot_path=SNAPSHOT, failure_path=FAILURES, *, preflight=False):
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with FileLock(str(snapshot_path.parent / ".refresh.lock"), timeout=0):
            return _refresh_locked(config_path, snapshot_path, failure_path, preflight)
    except Timeout:
        return False, "A refresh is already running."


def _refresh_locked(config_path, snapshot_path, failure_path, preflight):
    started = utc_now()
    LOG.info("%s started at %s", "Preflight" if preflight else "Refresh", started.isoformat(timespec="seconds"))
    try:
        with config_path.open(encoding="utf-8") as handle:
            config = yaml.safe_load(handle)
        start = pd.Timestamp(config["start_month"])
        end = pd.Timestamp(started.date())
        frame, records = collect(config, start, end)
        if records["policy_us_lower"]["latest_native_date"] != records["policy_us_upper"]["latest_native_date"]:
            raise DataError("U.S. policy target bounds end on different dates.")
        if (frame["policy_us_lower"] > frame["policy_us_upper"]).any():
            raise DataError("U.S. policy target lower bound exceeds its upper bound.")
        metadata = {"series": records}
        for year in BASE_YEARS:
            _, decomposition = calculate(frame, metadata, year)
            LOG.info("Base %s | latest complete common month %s | nominal %.8f | inflation %.8f | real %.8f",
                     year, decomposition["latest_month"].strftime("%Y-%m"),
                     decomposition["nominal"], decomposition["inflation"], decomposition["real"])
        if preflight:
            LOG.info("Preflight passed. No snapshot written.")
            return True, "Data preflight passed."
        if snapshot_path.exists():
            previous, previous_metadata = load_snapshot(snapshot_path)
            still_observed = frame.reindex(index=previous.index, columns=previous.columns).notna()
            lost = (previous.notna() & ~still_observed).sum()
            if lost.any():
                raise DataError(f"Refresh would erase published monthly observations: {lost[lost > 0].to_dict()}")
            regressed = [
                key for key, record in records.items()
                if record["latest_native_date"] < previous_metadata["series"][key]["latest_native_date"]
            ]
            if regressed:
                raise DataError(f"Refresh would move latest source dates backward: {regressed}")
        successful = utc_now().isoformat(timespec="seconds")
        metadata["last_successful_refresh_utc"] = successful
        rows = frame.reset_index()
        rows["month"] = rows["month"].dt.strftime("%Y-%m-%d")
        observations = rows.astype(object).where(rows.notna(), None).to_dict(orient="records")
        json_write(snapshot_path, {"schema_version": 1, "metadata": metadata, "observations": observations})
        LOG.info("Refresh succeeded at %s | published %s monthly rows to %s", successful, len(rows), snapshot_path.name)
        return True, f"Snapshot refreshed at {successful}."
    except Exception as error:
        message = safe_error(error)
        LOG.error("%s failed | %s", "Preflight" if preflight else "Refresh", message)
        if not preflight:
            failure_path.parent.mkdir(parents=True, exist_ok=True)
            with failure_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps({"timestamp_utc": utc_now().isoformat(timespec="seconds"), "error": message}) + "\n")
        return False, message


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true", help="Test and report the live inputs without writing a snapshot.")
    parser.add_argument("--log", type=Path, help="Also write the execution log to this file.")
    args = parser.parse_args()
    handlers = [logging.StreamHandler()]
    if args.log:
        args.log.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(args.log, mode="w", encoding="utf-8"))
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s", handlers=handlers)
    success, _ = refresh(preflight=args.preflight)
    raise SystemExit(0 if success else 1)


if __name__ == "__main__":
    main()
