"""
Climate Resilience of Himalayan Tourism - data cleaning pipeline
Author: Sneha Chaudhary

Reads the three raw sources in data/raw/, fixes known data-quality problems, and writes
tidy, Power BI-ready tables to data/processed/. Nothing is simulated: if a raw file is
missing the pipeline stops with an error instead of inventing data.

Run from the project root:  python src/data_preprocessing.py
"""

import os
import calendar

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "data", "raw")
PROCESSED_DIR = os.path.join(ROOT, "data", "processed")

TOURISM_FILE = "uttarakhand_district_tourism.csv"
RAINFALL_FILE = "uttarakhand_rainfall_summary.csv"
LANDSLIDE_FILE = "uttarakhand_landslide_events.csv"

# Rainfall source uses census/GADM spellings; tourism data uses the tourism department's names
DISTRICT_NAME_MAP = {
    "Hardwar": "Haridwar",
    "Garhwal": "Pauri Garhwal",
    "TehriGarhwal": "Tehri Garhwal",
    "UdhamSinghNagar": "Udham Singh Nagar",
}

# Almora and Nainital values are swapped for 2008-2010 in the source table: Almora jumps from
# ~94k to ~620k visitors and back to ~103k in 2011, while Nainital mirrors it. Swapping the two
# rows restores continuous series for both districts.
SWAPPED_ROWS = {"districts": ("Almora", "Nainital"), "years": (2008, 2009, 2010)}

# Values that look odd but are real events, so they are labelled rather than "fixed"
KNOWN_EVENTS = {
    ("Haridwar", 2010): "Kumbh Mela",
    ("Haridwar", 2021): "Kumbh Mela (during COVID-19)",
}


def load_tourism(path: str) -> pd.DataFrame:
    """
    Reads the wide district table (District, '2000 Indian', '2000 Foreign', '2000 Total', ...)
    and reshapes it to one row per District x Year with Indian, Foreign, Total columns.
    The file is read as CSV regardless of extension (it was previously misnamed .xlsx).
    """
    wide = pd.read_csv(path)
    wide.columns = [" ".join(str(c).split()) for c in wide.columns]  # '2024    Indian' -> '2024 Indian'
    wide["District"] = wide["District"].str.strip()

    long = wide.melt(id_vars="District", var_name="column", value_name="Visitors")
    long[["Year", "Visitor_Type"]] = long["column"].str.split(" ", n=1, expand=True)
    long["Year"] = long["Year"].astype(int)
    long["Visitors"] = pd.to_numeric(long["Visitors"], errors="coerce")

    tidy = (
        long.pivot_table(index=["District", "Year"], columns="Visitor_Type", values="Visitors", aggfunc="first")
        .reset_index()
        .rename_axis(columns=None)
    )
    # Years with no Total column in the source (2019) come back as missing after the pivot
    tidy = tidy.set_index(["District", "Year"]).reindex(
        pd.MultiIndex.from_product([tidy["District"].unique(), sorted(long["Year"].unique())], names=["District", "Year"])
    ).reset_index()
    if "Total" not in tidy:
        tidy["Total"] = np.nan
    return tidy[["District", "Year", "Indian", "Foreign", "Total"]]


def clean_tourism(tidy: pd.DataFrame) -> pd.DataFrame:
    """Fixes the known problems and records every change in a Quality_Note column."""
    df = tidy.copy()
    df["Quality_Note"] = ""

    # 1. Reconstruct missing totals (the 2019 'Total' column does not exist in the source)
    missing_total = df["Total"].isna() & df["Indian"].notna() & df["Foreign"].notna()
    df.loc[missing_total, "Total"] = df.loc[missing_total, "Indian"] + df.loc[missing_total, "Foreign"]
    df.loc[missing_total, "Quality_Note"] = "Total reconstructed as Indian + Foreign"

    # 2. Undo the Almora/Nainital row swap
    a, b = SWAPPED_ROWS["districts"]
    cols = ["Indian", "Foreign", "Total"]
    for year in SWAPPED_ROWS["years"]:
        ia = df.index[(df["District"] == a) & (df["Year"] == year)][0]
        ib = df.index[(df["District"] == b) & (df["Year"] == year)][0]
        row_a, row_b = df.loc[ia, cols].copy(), df.loc[ib, cols].copy()
        df.loc[ia, cols], df.loc[ib, cols] = row_b.values, row_a.values
        df.loc[[ia, ib], "Quality_Note"] = f"{a}/{b} values swapped back (source rows were interchanged)"

    # 3. Flag suspicious round-number estimates
    round_estimate = (df["Total"] % 100000 == 0) & (df["Foreign"] == 0)
    df.loc[round_estimate, "Quality_Note"] = "Looks like a rounded estimate (exact 100k multiple, zero foreign)"

    # 4. Label real events so they are not mistaken for errors
    for (district, year), event in KNOWN_EVENTS.items():
        df.loc[(df["District"] == district) & (df["Year"] == year), "Quality_Note"] = f"Event: {event}"

    # 5. Consistency check: Total must equal Indian + Foreign
    mismatch = (df["Indian"] + df["Foreign"] - df["Total"]).abs() > 0
    if mismatch.any():
        raise ValueError(f"Total != Indian + Foreign for {mismatch.sum()} rows:\n{df[mismatch]}")

    for col in cols:
        df[col] = df[col].astype("int64")

    df = df.sort_values(["District", "Year"]).reset_index(drop=True)
    df["Foreign_Share_pct"] = (df["Foreign"] / df["Total"] * 100).round(2)
    df["YoY_Change_pct"] = (df.groupby("District")["Total"].pct_change() * 100).round(2)
    return df


def load_rainfall(path: str) -> pd.DataFrame:
    """
    The raw rainfall summary has, per district-year:
      Average_Rainfall_mm  mean DAILY rainfall over the district's grid cells
      Total_Rainfall_mm    sum over every grid cell and day
    Total / Average equals days_in_year x number_of_grid_cells, so 'Total' grows with district
    AREA and must not be compared across districts. Real annual rainfall = daily mean x days.
    """
    df = pd.read_csv(path)
    df = df.rename(columns={"NAME_2": "District_Name"})
    df["District"] = df["District_Name"].replace(DISTRICT_NAME_MAP)

    days = df["Year"].map(lambda y: 366 if calendar.isleap(int(y)) else 365)
    df["Grid_Cells"] = (df["Total_Rainfall_mm"] / df["Average_Rainfall_mm"] / days).round().astype(int)
    df["Annual_Rainfall_mm"] = (df["Average_Rainfall_mm"] * days).round(1)

    # Anomaly relative to each district's own 2011-2024 normal
    stats = df.groupby("District")["Annual_Rainfall_mm"].agg(["mean", "std"])
    df = df.join(stats, on="District")
    df["Rainfall_Anomaly_pct"] = ((df["Annual_Rainfall_mm"] / df["mean"] - 1) * 100).round(2)
    df["Rainfall_Z"] = ((df["Annual_Rainfall_mm"] - df["mean"]) / df["std"]).round(3)

    return df[["District", "Year", "Annual_Rainfall_mm", "Rainfall_Anomaly_pct", "Rainfall_Z",
               "Average_Rainfall_mm", "Grid_Cells"]].rename(columns={"Average_Rainfall_mm": "Mean_Daily_Rainfall_mm"})


def load_landslides(path: str) -> pd.DataFrame:
    """
    State-level landslide counts by year. The rows come from different methods (a 1998
    field-mapping inventory, event-based counts, monsoon-season counts), so they are kept
    with their 'Type' and must not be summed into one total.
    """
    df = pd.read_csv(path)
    df["Landslides"] = pd.to_numeric(df["Landslides"], errors="coerce").astype("Int64")
    df["Comparable_Event_Count"] = df["Type"].str.startswith("Event-based")
    return df.sort_values("Year").reset_index(drop=True)


def build_panel(tourism: pd.DataFrame, rainfall: pd.DataFrame, landslides: pd.DataFrame) -> pd.DataFrame:
    """District x Year panel (2011-2024) joining tourism with rainfall, plus state landslide counts."""
    unmatched = set(tourism["District"]) - set(rainfall["District"])
    if unmatched:
        raise ValueError(f"Tourism districts without rainfall data: {unmatched}")
    panel = tourism.merge(rainfall, on=["District", "Year"], how="inner", validate="one_to_one")
    panel = panel.merge(landslides[["Year", "Landslides", "Type"]].rename(
        columns={"Landslides": "State_Landslides", "Type": "Landslide_Count_Type"}), on="Year", how="left")
    return panel


def run_etl_pipeline(raw_dir: str = RAW_DIR, out_dir: str = PROCESSED_DIR) -> dict:
    for name in (TOURISM_FILE, RAINFALL_FILE, LANDSLIDE_FILE):
        if not os.path.exists(os.path.join(raw_dir, name)):
            raise FileNotFoundError(f"Missing raw file: {os.path.join(raw_dir, name)}")

    tourism = clean_tourism(load_tourism(os.path.join(raw_dir, TOURISM_FILE)))
    rainfall = load_rainfall(os.path.join(raw_dir, RAINFALL_FILE))
    landslides = load_landslides(os.path.join(raw_dir, LANDSLIDE_FILE))
    panel = build_panel(tourism, rainfall, landslides)

    os.makedirs(out_dir, exist_ok=True)
    outputs = {
        "tourism_district_year.csv": tourism,
        "rainfall_district_year.csv": rainfall,
        "landslides_by_year.csv": landslides,
        "district_year_panel.csv": panel,
    }
    for name, frame in outputs.items():
        frame.to_csv(os.path.join(out_dir, name), index=False)

    print(f"Tourism:    {len(tourism):>4} rows ({tourism['District'].nunique()} districts, "
          f"{tourism['Year'].min()}-{tourism['Year'].max()}), {int((tourism['Quality_Note'] != '').sum())} rows annotated")
    print(f"Rainfall:   {len(rainfall):>4} rows ({rainfall['District'].nunique()} districts, "
          f"{rainfall['Year'].min()}-{rainfall['Year'].max()})")
    print(f"Landslides: {len(landslides):>4} rows (state level, mixed methods)")
    print(f"Panel:      {len(panel):>4} rows -> {out_dir}")
    return outputs


if __name__ == "__main__":
    run_etl_pipeline()
