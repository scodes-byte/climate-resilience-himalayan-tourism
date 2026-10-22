"""
Climate Resilience of Himalayan Tourism - analysis
Author: Sneha Chaudhary

Uses the cleaned tables from data/processed/ to answer three questions:
  1. How hard did the 2013 Kedarnath disaster and COVID-19 hit each district, and how fast did it recover?
  2. Is there a measurable year-to-year link between rainfall anomalies and tourist numbers?
  3. Which districts are most / least resilient (transparent composite index)?

Writes data/processed/district_resilience.csv and charts to reports/figures/.
Run from the project root after the ETL:  python src/analysis.py
"""

import os

import numpy as np
import pandas as pd
from scipy import stats

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(ROOT, "data", "processed")
FIGURES_DIR = os.path.join(ROOT, "reports", "figures")

RECOVERY_THRESHOLD = 0.90  # "recovered" = back to 90% of the pre-shock baseline

# (baseline year, trough window, window in which recovery is searched)
SHOCKS = {
    "Kedarnath_2013": {"baseline": 2012, "trough": (2013, 2015), "recovery": (2014, 2019)},
    "COVID_2020": {"baseline": 2019, "trough": (2020, 2021), "recovery": (2021, 2024)},
}
COVID_YEARS = {2020, 2021, 2022}


def shock_recovery(tourism: pd.DataFrame, baseline: int, trough: tuple, recovery: tuple) -> pd.DataFrame:
    """
    Event study per district:
      Drop_pct        = (trough visitors / baseline visitors - 1) * 100
      Recovery_Year   = first year in the recovery window with visitors >= 90% of baseline
      Years_To_Recover= Recovery_Year - baseline year (NaN if not recovered within the window)
    """
    rows = []
    for district, g in tourism.groupby("District"):
        series = g.set_index("Year")["Total"]
        base = series[baseline]
        window = series.loc[trough[0]:trough[1]]
        trough_year = int(window.idxmin())
        recovered = series.loc[max(trough_year + 1, recovery[0]):recovery[1]]
        recovered = recovered[recovered >= RECOVERY_THRESHOLD * base]
        rec_year = int(recovered.index[0]) if len(recovered) else np.nan
        rows.append({
            "District": district,
            "Baseline_Visitors": int(base),
            "Trough_Year": trough_year,
            "Trough_Visitors": int(window.min()),
            "Drop_pct": round((window.min() / base - 1) * 100, 1),
            "Recovery_Year": rec_year,
            "Years_To_Recover": rec_year - baseline if not np.isnan(rec_year) else np.nan,
        })
    return pd.DataFrame(rows)


def rainfall_tourism_correlation(panel: pd.DataFrame) -> dict:
    """
    Spearman rank correlation between a district's rainfall anomaly and its tourist YoY change
    in the same year. COVID years and Kumbh Mela years are excluded because they dominate the
    variation in visitors for non-climate reasons. Spearman is used because both variables are
    skewed and the relationship need not be linear.
    """
    data = panel[~panel["Year"].isin(COVID_YEARS) & ~panel["Quality_Note"].fillna("").str.startswith("Event")]
    data = data.dropna(subset=["Rainfall_Anomaly_pct", "YoY_Change_pct"])
    rho, p = stats.spearmanr(data["Rainfall_Anomaly_pct"], data["YoY_Change_pct"])

    no_2013 = data[data["Year"] != 2013]
    rho_ex, p_ex = stats.spearmanr(no_2013["Rainfall_Anomaly_pct"], no_2013["YoY_Change_pct"])
    return {
        "n": len(data), "rho": round(float(rho), 3), "p_value": round(float(p), 4),
        "n_excl_2013": len(no_2013), "rho_excl_2013": round(float(rho_ex), 3), "p_value_excl_2013": round(float(p_ex), 4),
    }


def min_max(series: pd.Series) -> pd.Series:
    span = series.max() - series.min()
    return (series - series.min()) / span if span else series * 0


def resilience_index(tourism: pd.DataFrame, rainfall: pd.DataFrame) -> pd.DataFrame:
    """
    Composite Resilience Index (0-100, higher = more resilient). Four components, each min-max
    scaled across districts so units do not matter, then averaged with equal weights:
      - depth of the 2013 Kedarnath shock (smaller drop = better)
      - years to recover from 2013 (not recovered by 2019 counts as 7 years)
      - depth of the COVID-19 shock
      - rainfall variability: coefficient of variation of annual rainfall (lower = better)
    Equal weights are a simple, explainable default; ranks should be checked for sensitivity.
    """
    ked = shock_recovery(tourism, **SHOCKS["Kedarnath_2013"]).set_index("District")
    cov = shock_recovery(tourism, **SHOCKS["COVID_2020"]).set_index("District")
    rain_cv = rainfall.groupby("District")["Annual_Rainfall_mm"].agg(lambda s: s.std() / s.mean() * 100)

    df = pd.DataFrame({
        "Kedarnath_Drop_pct": ked["Drop_pct"],
        "Kedarnath_Years_To_Recover": ked["Years_To_Recover"].fillna(7),
        "Kedarnath_Recovered_By_2019": ked["Recovery_Year"].notna(),
        "COVID_Drop_pct": cov["Drop_pct"],
        "COVID_Recovery_Year": cov["Recovery_Year"],
        "Rainfall_CV_pct": rain_cv.reindex(ked.index).round(2),
    })
    components = pd.DataFrame({
        "shock_2013": min_max(-df["Kedarnath_Drop_pct"]).rsub(1),  # drops are negative: deeper drop -> 1 -> score 0
        "recovery_2013": 1 - min_max(df["Kedarnath_Years_To_Recover"]),
        "shock_covid": min_max(-df["COVID_Drop_pct"]).rsub(1),
        "rain_variability": 1 - min_max(df["Rainfall_CV_pct"]),
    })
    df["Resilience_Index"] = (components.mean(axis=1) * 100).round(1)
    df["Rank"] = df["Resilience_Index"].rank(ascending=False, method="min").astype(int)
    return df.sort_values("Rank").reset_index()


def make_figures(tourism, rainfall, landslides, resilience):
    os.makedirs(FIGURES_DIR, exist_ok=True)

    # 1. State-wide visitors with key events
    state = tourism.groupby("Year")["Total"].sum() / 1e6
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(state.index, state.values, marker="o", color="#0F4C81")
    for year, label in [(2010, "Kumbh Mela"), (2013, "Kedarnath disaster"), (2020, "COVID-19"), (2021, "Kumbh + COVID")]:
        ax.annotate(label, (year, state[year]), textcoords="offset points", xytext=(0, 12), ha="center", fontsize=8)
    ax.set_title("Uttarakhand: total tourist visits, 11 districts")
    ax.set_ylabel("Visitors (millions)")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "state_tourism_trend.png"), dpi=130)
    plt.close(fig)

    # 2. 2013 shock, indexed to 2012 = 100, for the Char Dham districts vs the rest
    pivot = tourism.pivot(index="Year", columns="District", values="Total").loc[2010:2019]
    indexed = pivot / pivot.loc[2012] * 100
    fig, ax = plt.subplots(figsize=(10, 4.5))
    hit = ["Rudraprayag", "Chamoli", "Uttarkashi"]
    for district in indexed.columns:
        ax.plot(indexed.index, indexed[district], color="#EF4444" if district in hit else "#94A3B8",
                linewidth=2.2 if district in hit else 1, label=district if district in hit else None)
    ax.axhline(100, color="black", linewidth=0.8, linestyle="--")
    ax.axvline(2013, color="#F59E0B", linewidth=1)
    ax.set_title("Visitors indexed to 2012 = 100 (grey = other districts)")
    ax.set_ylabel("Index")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "kedarnath_2013_shock.png"), dpi=130)
    plt.close(fig)

    # 3. Annual rainfall (state mean of districts) with landslide event years
    rain = rainfall.groupby("Year")["Annual_Rainfall_mm"].mean()
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.bar(rain.index, rain.values, color=["#EF4444" if y in (2013, 2021) else "#0D9488" for y in rain.index])
    ax.set_title("Mean annual rainfall across Uttarakhand districts (red: 2013 Kedarnath, 2021 Chamoli disasters)")
    ax.set_ylabel("mm per year")
    ax.set_ylim(0, rain.max() * 1.15)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "annual_rainfall.png"), dpi=130)
    plt.close(fig)

    # 4. Resilience ranking
    fig, ax = plt.subplots(figsize=(8, 5))
    ordered = resilience.sort_values("Resilience_Index")
    ax.barh(ordered["District"], ordered["Resilience_Index"], color="#6366F1")
    ax.set_xlabel("Resilience Index (0-100)")
    ax.set_title("Composite tourism resilience index by district")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "resilience_index.png"), dpi=130)
    plt.close(fig)


def main():
    tourism = pd.read_csv(os.path.join(PROCESSED_DIR, "tourism_district_year.csv"))
    rainfall = pd.read_csv(os.path.join(PROCESSED_DIR, "rainfall_district_year.csv"))
    landslides = pd.read_csv(os.path.join(PROCESSED_DIR, "landslides_by_year.csv"))
    panel = pd.read_csv(os.path.join(PROCESSED_DIR, "district_year_panel.csv"))

    pd.set_option("display.width", 200)
    for name, params in SHOCKS.items():
        result = shock_recovery(tourism, **params)
        result.to_csv(os.path.join(PROCESSED_DIR, f"shock_{name.lower()}.csv"), index=False)
        print(f"\n== {name}: drop vs {params['baseline']} and recovery to {RECOVERY_THRESHOLD:.0%} ==")
        print(result.sort_values("Drop_pct").to_string(index=False))

    corr = rainfall_tourism_correlation(panel)
    print("\n== Rainfall anomaly vs tourist YoY change (Spearman, excl. COVID & Kumbh years) ==")
    print(corr)

    resilience = resilience_index(tourism, rainfall)
    resilience.to_csv(os.path.join(PROCESSED_DIR, "district_resilience.csv"), index=False)
    print("\n== Resilience index ==")
    print(resilience.to_string(index=False))

    make_figures(tourism, rainfall, landslides, resilience)
    print(f"\nFigures written to {FIGURES_DIR}")


if __name__ == "__main__":
    main()
