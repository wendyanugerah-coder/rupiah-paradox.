# Verification report

**Run date** · November 25, 2026 (America/Chicago). The submitted snapshot was refreshed successfully at 9:28:07 p.m. CST, November 26 at 03:28:07 UTC. Its latest complete common month for the exchange rate and both CPI levels is October 2026. Individual feed checks preceded dashboard implementation. The integrated preflight and refresh output is preserved in `preflight.log` and `refresh.log`.

## Data availability and quality

| Input | Coverage in the submitted snapshot | Latest native observation | Status |
| --- | --- | --- | --- |
| BI JISDOR | 3,123 daily fixings, Jan 2014–Nov 2026 | Nov 25, 2026 · 18,303 IDR/USD | Nov partial |
| BPS linked all-items CPI | 154 monthly levels, Jan 2014–Oct 2026 | Oct 2026 · 150.517038, Jan 2014 = 100 | Full history |
| BLS CPI-U NSA | 153 monthly levels, Jan 2014–Oct 2026 | Oct 2026 · 337.511 | Oct 2025 unavailable |
| IMF MYR/USD | 154 monthly averages, Jan 2014–Oct 2026 | Oct 2026 · 4.08177727 | Full history |
| IMF THB/USD | 154 monthly averages, Jan 2014–Oct 2026 | Oct 2026 · 33.64323158 | Full history |
| IMF PHP/USD | 154 monthly averages, Jan 2014–Oct 2026 | Oct 2026 · 63.09963636 | Full history |
| BI designated policy rate | 154 month-end rates, Jan 2014–Oct 2026 | Oct 2026 · 5.75% | Nov month-end pending |
| Fed target lower bound | 4,712 daily observations, Jan 2014–Nov 2026 | Nov 25, 2026 · 3.75% | Nov partial |
| Fed target upper bound | 4,712 daily observations, Jan 2014–Nov 2026 | Nov 25, 2026 · 4.00% | Nov partial |
| Fed nominal broad dollar | 3,210 daily published values, Jan 2014–Nov 2026 | Nov 20, 2026 · 123.5978 | Nov partial |

All 10 inputs passed the final integrated availability, coverage, frequency and three-calendar-month freshness checks. An early exploratory request to BI’s direct service returned HTTP 503. The integrated preflight and refresh both used BI’s direct service successfully. Independently hosted JISDOR extracts served as distribution cross-checks. The submitted code retrieves directly from BI and preserves the last snapshot if that route fails.

JISDOR had 11 expected publication days in June 2018. From 21 weekdays, Pancasila Day on June 1, eight weekdays during the June 11–20 Eid closure, and the June 27 election holiday account for the missing weekdays. The dashboard uses 11 as the coverage threshold for that month. [Cabinet Secretariat Eid notice](https://setkab.go.id/libur-mulai-11-20-juni-cuti-bersama-lebaran-2018-tambah-3-hari/) · [Election holiday decree notice](https://www.setneg.go.id/baca/index/siaran_pers_presiden_tetapkan_hari_libur_nasional_tanggal_27_juni_2018_melalui_keppres_nomor_15_tahun_2018) · [Bank Indonesia working-day notes](https://www.bi.go.id/id/publikasi/peraturan/Documents/Lampiran_PADG_203818.pdf)

## Original publication checks

Each original observation is matched to the configured series in the corresponding row below. Displayed monthly aggregates are identified separately from their underlying observations. Retrieval endpoints and series identifiers are in `config.yaml`.

### Indonesia FX and policy rates

| Series or instrument | Observation date | Original official value and publication | Retrieved value | Verification |
|---|---|---|---|---|
| JISDOR | 2026-11-25 | 18,303 IDR/USD in the [Bank Indonesia JISDOR bulletin](https://www.bi.go.id/en/statistik/informasi-kurs/jisdor/Default.aspx) | 18,303 IDR/USD | Exact |
| JISDOR | 2026-11-24 | 18,204 IDR/USD in the [Bank Indonesia JISDOR bulletin](https://www.bi.go.id/en/statistik/informasi-kurs/jisdor/Default.aspx) | 18,204 IDR/USD | Exact |
| Original BI Rate | 2015-01, decision Jan 15 | 7.75% retained in the [January 2015 Monetary Policy Review](https://www.bi.go.id/en/publikasi/laporan/Pages/Monetary-Policy-Review-January-2015.aspx) | 7.75% | Exact |
| Original BI Rate | 2016-07, decision Jul 21 | 6.50% retained in the [July 2016 BI decision](https://www.bi.go.id/id/publikasi/ruang-media/news-release/Pages/SP_185616.aspx) | 6.50% | Exact |
| BI 7-Day Reverse Repo Rate | 2016-08, effective Aug 19 | 5.25% as the new official policy rate in the [BI transition report](https://www.bi.go.id/en/publikasi/laporan/pages/monetary-policy-report-quarter-ii-2016.aspx) | 5.25% | Exact |
| BI-Rate, renamed BI 7-Day Reverse Repo Rate | 2026-10, decision Oct 21 | 5.75% retained in the [October 2026 BI decision](https://www.bi.go.id/en/publikasi/ruang-media/news-release/Pages/sp_2823326.aspx) | 5.75% | Exact |

JISDOR monthly values are arithmetic means of published daily fixings. In January 2015, 21 fixings summed to 264,161 for 12,579.095238095 IDR/USD. In October 2026, 22 fixings summed to 395,905 for 17,995.681818182 IDR/USD. In November 2026, 18 fixings through November 25 summed to 327,491 for a provisional 18,193.944444444 IDR/USD. Bank Indonesia changed its JISDOR collection methodology beginning April 5, 2021. It occasionally uses an earlier day's data under its publication rules, as occurred on November 26 and December 17, 2021. These are official fixings. [Bank Indonesia methodology](https://www.bi.go.id/en/fungsi-utama/moneter/informasi-kurs/default.aspx)

The July 2016 end-of-month value is the original BI Rate. The BI 7-Day Reverse Repo Rate took over as the designated policy rate on August 19, 2016, so the August end-of-month value is the repo rate. Bank Indonesia reported 6.50% for the legacy rate in July and 5.25% for the seven-day repo rate in August. The change reflects the instrument switch. Both sides of the comparison use an announced policy rate to measure policy stance. Differences in tenor and operating frameworks matter when interpreting the spread. The December 21, 2023 change to the BI-Rate label preserved the 7-day reverse repo framework. [Bank Indonesia policy-rate framework](https://www.bi.go.id/en/fungsi-utama/moneter/bi-rate/default.aspx)

### Statistics Indonesia national CPI

The dashboard retrieves BPS table `OTEzIzE=` directly. On November 25, 2026 Central time, the public endpoint returned HTTP 200 and 159,579 bytes in a Python Requests run. The English table has 250 monthly observations from January 2006 through October 2026. The January 2014 anchor supplies the lag for January 2015 year-over-year inflation. January 2014 through October 2026 contains 154 linked levels with no gaps. October 2026 was 25 calendar days before the run by comparison with the last day of its observation month. November 2026 was blank in the source and remains unavailable.

| BPS observation | Original release date | Original m/m (%) | Retrieved m/m (%) | Finding |
|---|---|---:|---:|---|
| January 2015 | February 2, 2015 | −0.24 | −0.24 | Exact match. [BPS January 2015 release](https://www.bps.go.id/en/pressrelease/2015/02/02/1102/januari-2015-terjadi-deflasi-0-24-persen.html) |
| February 2015 | March 2, 2015 | −0.36 | −0.36 | Exact match. [BPS February 2015 release](https://www.bps.go.id/en/pressrelease/2015/03/02/1118/februari-2015-terjadi-deflasi-0-36-persen.html) |
| January 2020 | February 3, 2020 | +0.39 | +0.39 | Exact match at first basket change. [BPS January 2020 release](https://www.bps.go.id/id/pressrelease/2020/02/03/1655/januari-2020-inflasi-) |
| January 2024 | February 1, 2024 | +0.04 | +0.04 | Exact match at second basket change. [BPS January 2024 release](https://www.bps.go.id/id/pressrelease/2024/02/01/2300/the-year-on-year--y-on-y--inflation-in-january-2024-was-2-57-percent--the-highest-inflation-by-province-was-seen-in-papua-tengah-province-at-4-76-percent-and-the-highest-inflation-by-regency-city-was-seen-in-toli-toli-regency-at-6-76-percent-.html) |
| October 2026 | November 2, 2026 | +0.22 | +0.22 | Exact match. [BPS October 2026 release](https://www.bps.go.id/id/pressrelease/2026/11/02/170347/inflasi-year-on-year-y-on-y-pada-oktober-2026-sebesar-3-23-persen.html) |

The BPS source expresses the national headline month-over-month changes to two decimal places. Set the linked index to 100 in January 2014, then multiply by `1 + published m/m percent / 100` each month. The scale therefore differs from the raw BPS reference-year indices. Changes across regimes retain the published transition-month growth rates. The underlying BPS basket was based on the 2012 household survey across 82 cities from January 2014, the 2018 survey across 90 cities from January 2020, and the 2022 survey across 150 districts and cities from January 2024. The splice removes artificial level jumps. Basket definitions and geographic coverage change at the transitions, and rounding can accumulate. Growth computed across a basket change may differ from published year-over-year growth calculated using a backcast new-basket comparator. For example, the January 2024 chain-derived value is 2.30% and the January 2024 BPS release reports 2.57%. The October 2026 linked index is 150.517038 and the linked year-over-year rate is 3.233285%, which rounds to the BPS published 3.23%. [BPS monthly table and methodology notes](https://www.bps.go.id/en/statistics-table/1/OTEzIzE=/monthly-national-consumer-price-inflation-rate--m-to-m--sup1-sup--2022-100-.html)

### U.S. CPI and Federal Reserve inputs

Preflight requested each configured FRED graph CSV independently from January 2014 on November 25, 2026 at 9:21 p.m. CST (November 26 at 03:21 UTC). All four requests returned HTTP 200. Dates below refer to the underlying observations. The CPI month is represented by its first day in the CSV.

| Series | Native observations and coverage within the requested window | Latest nonblank raw observation | Gaps and freshness |
| --- | --- | --- | --- |
| BLS all-items CPI-U, U.S. city average, NSA (`CPIAUCNS`) | 153 numeric monthly observations, Jan 2014–Oct 2026 | Oct 2026 · 337.511 | The CSV has a blank for Oct 2025 and has a numeric value in every other month in this window. Latest observation was one calendar month older than retrieval. |
| Federal funds target lower bound (`DFEDTARL`) | 4,712 daily calendar observations, Jan 1, 2014–Nov 25, 2026 | Nov 25, 2026 · 3.75% | Every calendar date in the requested span was present. November was in progress. |
| Federal funds target upper bound (`DFEDTARU`) | 4,712 daily calendar observations, Jan 1, 2014–Nov 25, 2026 | Nov 25, 2026 · 4.00% | Every calendar date in the requested span was present. November was in progress. |
| Nominal broad dollar index (`DTWEXBGS`) | 3,210 numeric weekday observations, Jan 2, 2014–Nov 20, 2026 | Nov 20, 2026 · 123.5978 | The feed included 152 blank rows, such as Nov 11, 2026. November contained 14 numeric observations and was in progress. The latest observation was dated five calendar days before retrieval and appeared in the November 23 weekly release. |

| Input | Observation | Original value | Retrieved value | Result | Original publication |
| --- | --- | ---: | ---: | --- | --- |
| BLS CPI-U NSA (`CPIAUCNS`) | Jan 2015 | 233.707 | 233.707 | Exact match | [BLS CPI release, Feb 26, 2015, Table 1, all items](https://www.bls.gov/news.release/archives/cpi_02262015.htm) |
| BLS CPI-U NSA (`CPIAUCNS`) | Sep 2025 | 324.800 | 324.800 | Exact match | [BLS CPI release, Oct 24, 2025, Table 1, all items](https://www.bls.gov/news.release/archives/cpi_10242025.htm) |
| BLS CPI-U NSA (`CPIAUCNS`) | Oct 2025 | Unpublished | Blank | Missingness matches | [BLS CPI release, Nov 10, 2026, Table 1, Oct 2025 column](https://www.bls.gov/news.release/archives/cpi_11102026.htm) |
| BLS CPI-U NSA (`CPIAUCNS`) | Oct 2026 | 337.511 | 337.511 | Exact match | [BLS CPI release, Nov 10, 2026, Table 1, all items](https://www.bls.gov/news.release/archives/cpi_11102026.htm) |
| Federal funds target lower bound (`DFEDTARL`) | Dec 17, 2015 | 0.25% | 0.25% | Exact match on effective date | [FOMC implementation note, Dec 16, 2015](https://www.federalreserve.gov/newsevents/pressreleases/20151216a1.htm) |
| Federal funds target upper bound (`DFEDTARU`) | Dec 17, 2015 | 0.50% | 0.50% | Exact match on effective date | [FOMC implementation note, Dec 16, 2015](https://www.federalreserve.gov/newsevents/pressreleases/20151216a1.htm) |
| Federal funds target lower bound (`DFEDTARL`) | Oct 29, 2026 | 3.75% | 3.75% | Exact match | [FOMC implementation note, Oct 28, 2026](https://www.federalreserve.gov/newsevents/pressreleases/monetary20261028a1.htm) |
| Federal funds target upper bound (`DFEDTARU`) | Oct 29, 2026 | 4.00% | 4.00% | Exact match | [FOMC implementation note, Oct 28, 2026](https://www.federalreserve.gov/newsevents/pressreleases/monetary20261028a1.htm) |
| Nominal broad dollar index (`DTWEXBGS`) | Nov 20, 2026 | 123.5978 | 123.5978 | Exact match | [Federal Reserve H.10, Nov 23, 2026, Memo row 1](https://www.federalreserve.gov/releases/h10/20261123/) |
| Nominal broad dollar index, average of daily inputs | Oct 2026 | 121.4781 | 121.4781428571 from 21 daily values | Match to publication precision | [Federal Reserve nominal broad dollar monthly table](https://www.federalreserve.gov/releases/h10/summary/jrxwtfb_nm.htm) |

U.S. CPI inflation uses `100 × (CPI[t] / CPI[t−12 calendar months] − 1)`. Both Oct 2025 and Oct 2026 U.S. YoY values remain blank because the first month lacks a numerator and the second month lacks a denominator. October 2026 CPI is available for the PPP level calculation. The shutdown also affected November 2025 collection and the BLS methodology for comparing some prices with an unavailable October reference period. [BLS shutdown methods](https://www.bls.gov/cpi/additional-resources/2025-federal-government-shutdown-impact-cpi-faq.htm)

The U.S. policy-rate measure is the arithmetic midpoint of the Federal Open Market Committee target range. On Oct 29, 2026 the matching bounds imply `(3.75 + 4.00) / 2 = 3.875%`, also the October month-end midpoint. This instrument measures the announced policy stance. [Federal Reserve implementation note](https://www.federalreserve.gov/newsevents/pressreleases/monetary20261028a1.htm)

The Federal Reserve's broad index covers a trade-weighted group of U.S. trading partners. We take the arithmetic average of published daily numeric observations. For November 2026 through Nov 20, the 14 available values averaged `122.3332571429`. The Fed reports a monthly series as an independent comparator and can revise the index history when weights change. [Federal Reserve index description and revision notes](https://www.federalreserve.gov/releases/h10/summary/)

### Regional exchange rates

Preflight used the IMF Exchange Rates dataset, SDMX 2.1, with `Accept: text/csv` and an explicit monthly date range. The source publishes monthly period averages in local currency units per U.S. dollar. Each series returned HTTP 200 and 154 observations from January 2014 through October 2026, with no missing months or duplicate months. The research window contains 142 observations per series. October 2026 was the latest released month observed on November 25, 2026 (America/Chicago). The three series passed the three-month freshness check. The dashboard uses the IMF monthly averages as published and divides each level by its selected base-month level before multiplying by 100. [IMF Exchange Rates](https://data.imf.org/en/datasets/IMF.STA:ER)

| IMF series | Observation date | Original official observation | Retrieved IMF observation | Result and original publication |
|---|---|---:|---:|---|
| `MYS.XDC_USD.PA_RT.M` | October 2026 | 4.0818 MYR/USD | 4.08177727272727 | Matches to four published decimal places. The mean of the 22 Bank Negara Malaysia noon midpoint rates is 4.0817772727272725. [BNM monthly publication on Malaysia's official portal](https://data.gov.my/data-catalogue/exchangerates), [monthly CSV](https://storage.data.gov.my/finsector/exr/monthly.csv), [daily CSV](https://storage.data.gov.my/finsector/exr/daily_1200.csv) |
| `THA.XDC_USD.PA_RT.M` | October 2026 | 33.6432 THB/USD | 33.6432315789474 | Matches to four published decimal places. Select Monthly and October 2026 for both dates in Bank of Thailand table FM_FX_001_S3, then read row 6 (`MID RATE`) under `USA : DOLLAR (USD)`. The legacy IMF IFS metadata identifies the commercial-bank midpoint as the relevant underlying quote. [Bank of Thailand statistical table](https://app.bot.or.th/BTWS_STAT/statistics/BOTWEBSTAT.aspx?language=ENG&reportID=123&secureweb=Symphony), [IMF IFS Thailand notes hosted by the UN Statistics Division](https://unstats.un.org/unsd/servicetradekb/attachments/Thailand-GUID5acba819ce9b45238ada70c4551ba4d8.pdf) |
| `PHL.XDC_USD.PA_RT.M` | October 2026 | 63.0996 PHP/USD | 63.0996363636364 | Matches to four published decimal places. Bangko Sentral ng Pilipinas Table 12, `Monthly Average`, `October`, 2026 column. [BSP Table 12](https://www.bsp.gov.ph/statistics/external/tab12_pus_data.aspx) |

## Independent February 2015 PPP and real depreciation check

The January 2015 base and February 2015 check use a separately downloaded copy of daily Bank Indonesia JISDOR, archived BPS CPI and archived BLS CPI-U. The independent JISDOR CSV reports extracting the fixings directly from Bank Indonesia. Its 40 dates and values for the test months match the January and February monthly values aggregated in the submitted snapshot. This is a second distribution check for the same underlying series. [Separate daily CSV](https://calcuid.com/data/kurs-pajak/jisdor-harian.csv) · [CSV publisher’s methodology](https://calcuid.com/kurs/pajak/) · [Bank Indonesia JISDOR](https://www.bi.go.id/en/statistik/informasi-kurs/jisdor/Default.aspx)

| Independent input | January 2015 | February 2015 |
| --- | ---: | ---: |
| JISDOR daily observations | 21 | 19 |
| Sum of IDR per USD fixing values | 264,161 | 242,247 |
| Arithmetic monthly mean IDR per USD | 12,579.0952380952 | 12,749.8421052632 |
| BPS published all-items CPI, 2012 = 100 | 118.71 | 118.28 |
| BPS official CPI growth from previous month | −0.24% | −0.36% |
| BLS all-items CPI-U NSA, 1982–84 = 100 | 233.707 | 234.722 |

The archive values came from the all-items row or national headline text. February is in the same BPS CPI base as January, which supplies a separate check using published index levels. [January BPS release](https://www.bps.go.id/id/pressrelease/2015/02/02/1102/januari-2015-terjadi-deflasi-0-24-persen.html), [February BPS release](https://www.bps.go.id/id/pressrelease/2015/03/02/1118/februari-2015-terjadi-deflasi-0-36-persen.html), [January BLS release](https://www.bls.gov/news.release/archives/cpi_02262015.htm), [February BLS release](https://www.bls.gov/news.release/archives/cpi_03242015.htm)

Using an independent Python `Decimal` calculation with 40-digit working precision, the dashboard's BPS chaining convention takes the official February month-over-month change and sets the February-to-January inflation factor to `0.9964`. Separately, the February-to-January U.S. CPI factor is `234.722 / 233.707`. Relative PPP in IDR/USD is `12,579.0952380952 × 0.9964 / (234.722 / 233.707)`. The real exchange rate ratio is computed directly as `(12,749.8421052632 / 12,579.0952380952) × (234.722 / 233.707) / 0.9964` using the unrounded inputs shown by the integer totals and counts.

| February 2015 result, January 2015 base | BPS growth-rate chaining | BPS published CPI levels (cross-check) |
| --- | ---: | ---: |
| Actual exchange rate index | 101.3573859164 | 101.3573859164 |
| Relative PPP level, IDR per USD | 12,479.6109841029 | 12,479.3320243982 |
| Relative PPP index | 99.2091302903 | 99.2069126451 |
| Real exchange rate index | 102.1653809682 | 102.1676647463 |
| Nominal depreciation, log % | +1.3482559601 | +1.3482559601 |
| Inflation contribution, log % | −0.7940136716 | −0.7962490203 |
| Real depreciation by subtraction, log % | +2.1422696317 | +2.1445049804 |
| Real depreciation from `100 × ln(q_Feb / q_Jan)`, log % | +2.1422696317 | +2.1445049804 |

**Result.** The direct real exchange rate and decomposition agree to the displayed precision for both sets of input. The difference of 0.00224 log percentage points between methods reflects rounding of the source's published CPI levels and growth rate. The calculations used the official growth-rate convention in the first result column.

## Independent check of the submitted endpoint

The following calculation reads the two rows directly from the JSON snapshot and uses Python `Decimal` with 45 digits of working precision. It is independent of the dashboard’s calculation function.

| Input | January 2015 | October 2026 |
| --- | ---: | ---: |
| JISDOR mean, IDR/USD | 12,579.095238095239 | 17,995.68181818182 |
| Linked BPS CPI, Jan 2014 = 100 | 106.95148890824142 | 150.51703810862927 |
| BLS CPI-U NSA, 1982–84 = 100 | 233.707 | 337.511 |
| Real exchange rate `q = S × CPI_US / CPI_ID` | 27,487.439780588118 | 40,352.511864822243 |

The relative inflation factor is `0.974501737073`. Multiplying the January rate by that factor gives a PPP-implied October rate of **12,258.350160330875 IDR/USD**. October’s actual index is **143.0602**, the PPP index **97.4502** and the real exchange rate index **146.8035**, with January 2015 = 100 throughout. The direct `100 × ln(q[t]/q[0])` and the nominal-minus-inflation residual both equal **38.392447960881 log percentage points** to 12 decimal places.

## Application and refresh checks

- All four base selections loaded six charts. The indexed lines start at 100 in each base month, and the October 2026 U.S. CPI level continues to support the PPP comparison while the two affected U.S. year-over-year values remain blank.
- A separate test injected a JISDOR connection failure against a copy of the snapshot. The refresh returned failure, wrote a separate failure record and preserved the prior snapshot byte-for-byte (`SHA-256 9d36c10787eaf58927d7277b294611ba38902aed8e38efb7d0df29a17b14be36`). A held refresh lock also blocked a concurrent write. These tests used an isolated copy of the data.
- The workflow YAML parsed with a daily schedule and manual trigger. The refresh was executed locally. It will run on GitHub after the project is added to an Actions-enabled repository with branch write access.

## Numerical material for the student’s memo

| January base | Latest complete common month | Nominal log change | Inflation contribution | Real log change |
| --- | --- | ---: | ---: | ---: |
| 2015 | Oct 2026 | +35.81 | −2.58 | +38.39 |
| 2017 | Oct 2026 | +29.80 | −6.24 | +36.04 |
| 2019 | Oct 2026 | +23.95 | −8.65 | +32.60 |
| 2021 | Oct 2026 | +24.67 | −9.11 | +33.78 |

- For the January 2015 base, the inflation component is **−7.21%** of the nominal log change. Relative inflation moves the benchmark toward rupiah appreciation and offsets 2.58 log points of the observed nominal depreciation in the accounting identity.
- For October 2026 and January 2015 = 100, the FX indices are **143.06 IDR**, **113.90 MYR**, **102.78 THB**, and **141.47 PHP**. Use a common month for comparison. The JISDOR November-to-date average is **18,193.94 IDR/USD** from 18 published fixings and is provisional.
- The BI–Fed month-end policy spread is **7.625 pp** in January 2015 and **1.875 pp** in October 2026. The October nominal broad dollar index is **121.4781**, compared with **103.7607** in January 2015 and **128.8370** at its January 2025 sample peak through October 2026.
- October 2026 linked Indonesian CPI inflation is **3.23% YoY**. The latest calculable U.S. YoY rate is **3.74%** in September 2026. The two figures refer to different months. Use matching months to compare inflation rates.

### Mechanisms and limitations to investigate

- **Common dollar conditions and risk appetite.** Compare turning points in the broad dollar and the four currencies. The dollar index uses a different basket and cannot identify the dollar’s causal contribution to the rupiah. BIS research discusses the dollar and emerging-market local-currency portfolio flows. [BIS Quarterly Review](https://www.bis.org/publications/qr-202409/us-dollar-and-capital-flows-emes)
- **Country-level flows.** Bank Indonesia and the IMF document episodes of portfolio flows and rupiah pressure. The dashboard contains no capital-flow series, commodity prices or policy surprises. These sources can supply dated evidence for a proposed channel. [Bank Indonesia Q3 2026 Monetary Policy Report](https://www.bi.go.id/en/publikasi/laporan/Pages/Laporan-Kebijakan-Moneter-Triwulan-III-2026.aspx) · [IMF 2025 Article IV staff report](https://www.elibrary.imf.org/view/journals/002/2026/010/article-A001-en.xml)
- **Interest parity and carry.** A nominal policy spread gives context for potential carry. A currency loss can offset yield, while risk premia, hedging costs, and access to funding affect returns. The spread is an illustrative policy measure and the dashboard provides neither investable yields nor forward quotes or market expectations. [Federal Reserve staff study](https://www.federalreserve.gov/econresdata/ifdp/2017/files/ifdp1196.pdf)
- **Identification and measurement.** The inflation contribution is an accounting term. The real residual can reflect exchange-rate shocks, risk premia, structural shifts, or CPI measurement. Relative PPP depends on the chosen base, and its gap alone cannot establish undervaluation. Linked CPI rates have rounding and basket-composition effects. The June 2018 calendar, October 2025 BLS gap and August 2016 BI instrument change are documented above.
