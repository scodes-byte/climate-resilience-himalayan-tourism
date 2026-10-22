import os
import sys

import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import data_preprocessing as etl  # noqa: E402
import analysis  # noqa: E402

RAW = os.path.join(ROOT, "data", "raw")


@pytest.fixture(scope="module")
def tourism():
    return etl.clean_tourism(etl.load_tourism(os.path.join(RAW, etl.TOURISM_FILE)))


@pytest.fixture(scope="module")
def rainfall():
    return etl.load_rainfall(os.path.join(RAW, etl.RAINFALL_FILE))


def test_tourism_shape_and_consistency(tourism):
    assert tourism["District"].nunique() == 11
    assert tourism["Year"].min() == 2000 and tourism["Year"].max() == 2024
    assert len(tourism) == 11 * 25
    assert (tourism["Indian"] + tourism["Foreign"] == tourism["Total"]).all()


def test_2019_totals_reconstructed(tourism):
    row = tourism[(tourism["District"] == "Dehradun") & (tourism["Year"] == 2019)].iloc[0]
    assert row["Total"] == 6754039 + 38989
    assert "reconstructed" in row["Quality_Note"]


def test_almora_nainital_swap_is_undone(tourism):
    almora = tourism[tourism["District"] == "Almora"].set_index("Year")["Total"]
    nainital = tourism[tourism["District"] == "Nainital"].set_index("Year")["Total"]
    # After the fix both series move smoothly (no >3x jump year to year around 2008-2011)
    for series in (almora, nainital):
        ratios = (series.loc[2007:2011] / series.loc[2007:2011].shift()).dropna()
        assert ratios.between(1 / 3, 3).all()


def test_kumbh_years_are_labelled_not_changed(tourism):
    row = tourism[(tourism["District"] == "Haridwar") & (tourism["Year"] == 2010)].iloc[0]
    assert row["Total"] == 18866680
    assert row["Quality_Note"].startswith("Event")


def test_rainfall_names_harmonised_and_units(rainfall, tourism):
    assert set(tourism["District"]) <= set(rainfall["District"])
    # Annual rainfall must be physically plausible for the Himalaya (roughly 500-3500 mm)
    assert rainfall["Annual_Rainfall_mm"].between(500, 3500).all()
    # Grid-cell count is a district property, so it must be constant across years
    assert (rainfall.groupby("District")["Grid_Cells"].nunique() == 1).all()


def test_panel_join_keeps_every_district(tourism, rainfall):
    landslides = etl.load_landslides(os.path.join(RAW, etl.LANDSLIDE_FILE))
    panel = etl.build_panel(tourism, rainfall, landslides)
    assert panel["District"].nunique() == 11
    assert len(panel) == 11 * 14  # 2011-2024


def test_landslide_methods_are_kept_apart():
    landslides = etl.load_landslides(os.path.join(RAW, etl.LANDSLIDE_FILE))
    field_mapping = landslides[landslides["Type"] == "Field-based mapping"]
    assert not field_mapping["Comparable_Event_Count"].any()


def test_missing_raw_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        etl.run_etl_pipeline(raw_dir=str(tmp_path), out_dir=str(tmp_path))


def test_shock_recovery_on_toy_data():
    toy = pd.DataFrame({
        "District": ["A"] * 6,
        "Year": [2012, 2013, 2014, 2015, 2016, 2017],
        "Total": [100, 40, 20, 60, 95, 120],
    })
    out = analysis.shock_recovery(toy, baseline=2012, trough=(2013, 2015), recovery=(2014, 2019)).iloc[0]
    assert out["Trough_Year"] == 2014
    assert out["Drop_pct"] == -80.0
    assert out["Recovery_Year"] == 2016
    assert out["Years_To_Recover"] == 4


def test_kedarnath_hit_districts_rank_lowest(tourism, rainfall):
    res = analysis.resilience_index(tourism, rainfall)
    bottom3 = set(res.sort_values("Resilience_Index").head(3)["District"])
    assert {"Rudraprayag", "Uttarkashi"} <= bottom3
    assert res["Resilience_Index"].between(0, 100).all()
