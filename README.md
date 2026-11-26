# The Rupiah Paradox

A Streamlit dashboard for comparing the Indonesian rupiah’s depreciation against the U.S. dollar with the relative purchasing power parity (PPP) benchmark and examining the remaining real depreciation. Select a January base month to update the indices and decomposition. January 2015 is the default.

## Run locally

With Python 3.12, open a terminal in this directory.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

The app opens with the included snapshot and supports a manual **Refresh official data** button. The command line provides the same refresh logic and a preflight mode.

```bash
python refresh.py --preflight
python refresh.py --log workflow-logs/refresh.log
```

## Daily updates

Commit the project to a GitHub repository with Actions enabled and give its workflow token permission to write contents to the selected branch. The workflow in `.github/workflows/refresh.yml` is scheduled daily at 5:23 p.m. CST or 6:23 p.m. CDT (23:23 UTC) on the default branch. It can also be started under **Actions → Refresh economic data → Run workflow**. A local Streamlit checkout uses its local snapshot. Pull the workflow’s commits into that checkout or configure the Streamlit host to redeploy from the branch to see scheduled updates there.

The selected official data endpoints are public and keyless. If a future provider requires an API key, supply it through an environment variable and map the matching GitHub Secret to that variable in the workflow. Keep credentials out of configuration, URLs, logs, and Git. GitHub Actions uses the built-in repository-scoped token for commits.

A refresh checks coverage, numerical validity, frequency, base-month availability, and recency. A validated snapshot and its UTC refresh timestamp replace the previous file in one atomic operation. If a feed fails, newly omits an expected historical month, or moves its latest date backward, the previous snapshot remains available. The refresh records the failure separately in `data/refresh_failures.jsonl` and exits with a nonzero status. GitHub Actions uploads the execution log and can commit a failure record while retaining the prior snapshot.

## Data and transformations

| Indicator | Series and monthly calculation |
| --- | --- |
| Nominal rate | Bank Indonesia JISDOR, daily IDR per USD. Arithmetic average of published business-day fixings. Higher means rupiah depreciation. |
| Inflation | BPS national all-items CPI growth and BLS all-items U.S. city average CPI-U, unadjusted, via FRED. Compute `100 × (CPI[t] / CPI[t−12 calendar months] − 1)` for each country. |
| Actual and relative PPP | `PPP[t] = S[0] × (CPI_ID[t]/CPI_ID[0]) / (CPI_US[t]/CPI_US[0])`. Divide the actual and PPP-implied rates by `S[0]` and multiply by 100. |
| Regional rates | JISDOR and IMF monthly period-average MYR, THB and PHP per USD. Divide each rate by its own base-month level and multiply by 100. Market conventions and fixing times differ by currency. |
| Policy spread | Bank Indonesia’s end-of-period policy rate via BIS minus the midpoint of the Federal Reserve’s federal funds target range via FRED. For the Fed, use the last available observation of each target bound in the calendar month. |
| Broad dollar | Federal Reserve H.10 nominal broad dollar index via FRED, January 2006 = 100. Arithmetic average of published daily observations. Higher means a stronger U.S. dollar against the broad trade-weighted basket. |

All retrieval URLs and IDs are in `config.yaml`. Dates are represented as first-of-month keys in the panel. Chart values for an open month are provisional and flagged. Daily-feed status also flags unusually sparse months and a last reported month with more than two weekdays remaining after its final observed date. June 2018 has a documented JISDOR publication-calendar exception. Monthly series can lag each other. Freshness compares the latest daily observation or the end of the latest monthly observation period with the date three calendar months earlier. See the data quality panel for the separate source dates and the verification report for the schedule and observations checked.

## Real depreciation accounting

Let `S` denote rupiah per U.S. dollar. The latest complete common month requires `S` and both CPI levels.

- Nominal depreciation is `100 × ln(S[t] / S[0])`.
- The inflation contribution is `100 × ln[(CPI_ID[t]/CPI_ID[0]) / (CPI_US[t]/CPI_US[0])]`.
- Real depreciation is the difference. It also equals `100 × ln(q[t] / q[0])`, where `q[t] = S[t] × CPI_US[t] / CPI_ID[t]`. `real_index` is `100 × q[t] / q[0]` and rises with real depreciation.

The contribution accounts for changes in relative prices by construction. The January base fixes the scale, and a change of base changes the reported cumulative movement. CPI indices depend on currency-specific baskets and their normalizations. Relative PPP and the real index change over the chosen interval have no absolute fair-value interpretation.

BPS publishes monthly national CPI growth rates to two decimals. The refresh starts January 2014 at 100 and chains each subsequent published monthly growth factor. The January 2020 and January 2024 growth rates link the 2012-, 2018-, and 2022-based baskets across breaks. Rounding can accumulate. A chained year-over-year calculation around a basket change can differ from the official comparison using a backcast new basket. BLS did not publish October 2025 all-items CPI during the U.S. federal shutdown. October 2025 and October 2026 U.S. year-over-year rates are both blank. The October 2026 CPI level is published and used for PPP. Monthly and yearly gaps are retained without interpolation.

The original BI Rate is used through July 2016. The BI 7-Day Reverse Repo Rate took over on August 19, 2016, and was renamed BI-Rate in December 2023. The August 2016 change partly reflects the instrument switch. The spread compares announced policy settings. The two countries’ instruments differ in tenor and operating framework. A carry trade depends on market borrowing and lending rates, the realized exchange rate, costs, and funding and risk conditions. The dashboard contains no forward quotes for a covered interest-parity test. Uncovered interest parity concerns expected exchange rate movements, so a realized depreciation alone cannot test it.

## Submission files

- `app.py`, `refresh.py`, `analysis.py`, and the source adapters contain the app, refresh, and calculation logic.
- `data/snapshot.json` contains the validated monthly inputs and source metadata. The app’s data quality panel downloads a CSV of inputs and calculations at any selected base.
- `data/monthly-jan2015.csv` is the frozen submission extract for the default base month, including 2014 inputs for year-over-year lags. The JSON snapshot is the file updated by future refreshes.
- `evidence/verification.md` records the source comparisons and independent calculations and provides numerical material for the student’s memo.
- `evidence/preflight.log` and `evidence/refresh.log` are terminal execution records. `evidence/dashboard.jpg` shows the running app.
