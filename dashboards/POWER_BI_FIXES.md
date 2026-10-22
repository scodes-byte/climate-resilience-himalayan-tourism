# Power BI dashboard: known issues and how to fix them

The `.pbix` in this folder is the original group-project dashboard. Its data model was inspected
(tables, Power Query steps and measures) and has the problems below. The `.pbix` file itself has not
been edited, because that requires Power BI Desktop. Follow these steps to rebuild it on the cleaned data.

## Problems found in the original model

| # | Problem | Effect |
|---|---------|--------|
| 1 | Sources point to files on a teammate's Desktop (`C:\Users\piyus\OneDrive\Desktop\...`) | The report cannot be refreshed on any other machine. |
| 2 | Rainfall district names (`Hardwar`, `Garhwal`, `TehriGarhwal`) don't match tourism names (`Haridwar`, `Pauri Garhwal`, `Tehri Garhwal`) | The rainfall→tourism relationship silently drops 3 districts, including Haridwar, the largest. |
| 3 | Visuals use `Total_Rainfall_mm` | That column is summed over grid cells, so it measures district **area**. Chamoli (12 cells) looks 6× wetter than Champawat (2 cells). |
| 4 | `Resilience Score = 50 − 0.2·rainfall − 0.5·landslides + 0.3·tourists` | Raw units are mixed. Tourists are in the millions, so the score is ≈ 0.3 × visitor count, a popularity ranking. Landslides have no district, so the same total is subtracted everywhere. |
| 5 | `Total landslides` card sums the landslide table | Rows mix a 1998 field-mapping inventory (1,419) with event counts, so the total isn't meaningful. |
| 6 | `Total_tourist` custom column sums the yearly totals except 2019 | The source has no 2019 Total column, so 2019 visitors are missing. |
| 7 | Power Query replaced the text `"455 + 1 = 456"` in the landslide sheet | A manual-entry error in the source; it's now stored cleanly in `data/raw/`. |

## Rebuild steps

1. Run `python src/data_preprocessing.py` and `python src/analysis.py`.
2. In Power BI: **Transform data → Data source settings** and repoint each source to `data/processed/`:
   `tourism_district_year.csv`, `rainfall_district_year.csv`, `landslides_by_year.csv`, `district_resilience.csv`.
   District names are already harmonised and 2019 totals reconstructed.
3. Create a `District` table (`DISTINCT(Tourism[District])`) and a `Year` table (`GENERATESERIES(2000, 2024, 1)`),
   and relate them one-to-many to the fact tables (see the header of `DAX_Measures_Library.dax`).
4. Delete the old `Resilience Score` measure and paste the measures from `DAX_Measures_Library.dax`.
5. Replace visuals:
   - "District wise rainfall comparison": use `[Avg Annual Rainfall (mm)]`, not the sum of `Total_Rainfall_mm`.
   - "Rainfall vs Tourist Relationship": put `District` and `Year` on details, `[Rainfall Anomaly %]` on X and
     `[YoY Visitor Change %]` on Y.
   - Map and gauge: use `[Resilience Index]` per district.
   - Landslide card: use `[Landslides (Event-based)]` and show the counting method in the tooltip.
6. Optionally apply `Himalayan_Climate_Theme.json` via **View → Themes → Browse for themes**.
