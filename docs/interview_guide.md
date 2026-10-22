# Climate Resilience of Himalayan Tourism: Interview Guide

Everything below matches the code and data in this repo. Before any interview, **write down in one line which parts
you personally did in the original group project** (data collection? Power BI? the poster?). Interviewers always ask,
and "the four of us split it as…" is a strong, honest answer. The Python pipeline and analysis in `src/` are your
later extension; say so.

---

## 1. The 60-second pitch

> "This started as a four-person university project on how climate disasters affect tourism in Uttarakhand.
> We combined 25 years of district tourism statistics with gridded rainfall data and landslide records, and built a
> Power BI dashboard.
>
> Afterwards I went back and rebuilt the data pipeline properly in Python, and found that a lot was wrong: the
> processed dataset was actually random numbers because a file had the wrong extension, two districts' rows were
> swapped for three years, and the rainfall measure in the dashboard was really measuring district size.
>
> With clean data, the findings are clear: the 2013 Kedarnath disaster wiped out 93% of visitors in Rudraprayag,
> which took about six years to recover, while Dehradun barely dipped. And ordinary rainfall variation doesn't
> explain tourism at all once you remove 2013. Extreme events matter, average weather doesn't. I turned that into
> a resilience index that ranks the pilgrimage districts as the most vulnerable."

---

## 2. The pipeline step by step

```
data/raw/ ──► src/data_preprocessing.py ──► data/processed/ ──► src/analysis.py ──► figures + resilience CSV ──► Power BI
```

**`data_preprocessing.py`**
1. `load_tourism`: the source is *wide* (one column per year × type: `2000 Indian`, `2000 Foreign`…). `melt` turns
   it into *long* format, then `pivot_table` makes one row per District × Year with Indian / Foreign / Total.
   Long ("tidy") format is what pandas, Power BI and charts all want.
2. `clean_tourism`: reconstruct 2019 totals, undo the Almora/Nainital swap, flag round-number estimates, label
   Kumbh Mela years, then **assert** Indian + Foreign = Total for every row (fail loudly, never silently).
3. `load_rainfall`: convert to real annual rainfall (mean daily × days), harmonise district names, compute the anomaly
   vs each district's own average and a z-score.
4. `load_landslides`: keep each count's method; mark which ones are comparable.
5. `build_panel`: join tourism + rainfall on District + Year with `validate="one_to_one"`, and error if any district
   is unmatched (this is exactly the bug that silently dropped Haridwar in Power BI).

**`analysis.py`**
- `shock_recovery`: event study per district (explained below).
- `rainfall_tourism_correlation`: Spearman correlation.
- `resilience_index`: composite index.
- `make_figures`: matplotlib charts for the README.

---

## 3. The data-quality story (the best part of this project in interviews)

| Problem | How I found it | Fix |
| --- | --- | --- |
| `.xlsx` file was actually CSV → read failed → script **silently generated random data** | `file` command / reading the bytes; the "processed" data had districts and years that weren't in the source | Read as CSV; pipeline now raises an error if data is missing instead of simulating |
| Almora & Nainital swapped 2008–10 | Almora jumped 94k → 622k → back to 103k; Nainital mirrored it | Swap back, record in `Quality_Note`, test that both series are now smooth |
| 2019 has no Total column | Pivot produced missing values | Total = Indian + Foreign, then validate every row |
| `Total_Rainfall_mm` ∝ district area | Total ÷ Average was always 365 × a whole number (the grid-cell count) | Use mean daily × days → 1,100–2,050 mm/yr, which is physically realistic |
| District names differ (`Hardwar`/`Haridwar`) | Join lost 3 districts | Name map + join that fails on unmatched keys |
| Kumbh Mela spikes (Haridwar 2010, 2021) | Outliers | **Not** an error: labelled, kept, excluded from the correlation |
| Landslide rows use different methods | `Type` column | Never summed together |

Lesson to say out loud: *"Outliers aren't automatically errors. I check whether there's a real-world explanation
(Kumbh Mela) or a data-entry explanation (swapped rows) before touching anything, and I log every change."*

---

## 4. The analysis, with numbers

### Event study (natural experiment)
- Baseline = the last normal year (2012 for Kedarnath, 2019 for COVID).
- Drop % = lowest year in the window ÷ baseline − 1.
- Recovery year = first year back at ≥ 90% of baseline.

| District | Kedarnath drop | Years to recover |
| --- | --- | --- |
| Rudraprayag (Kedarnath temple) | −93% | 6 |
| Chamoli (Badrinath) | −83% | 5 |
| Uttarkashi (Gangotri/Yamunotri) | −80% | 7 |
| Dehradun | −14% | 2 |
| Haridwar | −16% | 2 |

Why it works: the disaster was sudden and local, so neighbouring districts act as an informal comparison group.
(The formal version of this idea is *difference-in-differences*; mention it as the next step.)

### Correlation
- Rainfall anomaly (% above the district's own average) vs visitor YoY change, 121 district-years.
- **Spearman** (rank-based) because both variables are skewed and the link need not be linear.
- Result: ρ = −0.18, p = 0.053 overall → ρ = −0.01, p = 0.88 without 2013.
- Interpretation: one extreme year drives the whole relationship. **Correlation ≠ causation**, and an extreme event
  can create an apparent correlation on its own.
- Why exclude COVID (2020–22) and Kumbh years: they move visitor numbers for non-climate reasons and would swamp
  any climate signal.

### Resilience index
- Components: 2013 drop depth, 2013 recovery years, COVID drop depth, rainfall variability (coefficient of variation).
- Each one **min-max scaled** to 0–1 (so % and years become comparable), flipped so higher = better, averaged, × 100.
- Equal weights: simple and explainable; I'd test other weightings to check the ranking is stable.
- Why the old Power BI score was wrong: `50 − 0.2·rain − 0.5·landslides + 0.3·tourists` adds raw quantities with
  different units. Tourists are in the millions, so it just ranked districts by popularity. **Always normalise before
  combining indicators.**

---

## 5. Power BI talking points

- Original model: 3 tables, 1 relationship, 2 measures. I inspected it (Power Query M code and DAX) and documented
  7 problems in `dashboards/POWER_BI_FIXES.md`.
- Correct modelling: star schema with `District` and `Year` dimension tables, facts related one-to-many, single
  filter direction. That avoids ambiguous relationships and lets one slicer filter tourism and rainfall together.
- DAX concepts used: `CALCULATE` with `REMOVEFILTERS` to compute a fixed baseline (2012) regardless of the year
  slicer; `DIVIDE` for safe division; `SELECTEDVALUE` for previous-year logic on an integer year column.
- Hard-coded `C:\Users\...` paths break refresh: use parameters or relative/shared sources.

---

## 6. Likely interview questions

**Q: What was the most important thing you learned?**
Silent failure is the worst failure. The old script caught an error and generated fake data, and nobody noticed
because the dashboard still looked fine. Now the pipeline fails loudly and has tests.

**Q: How do you know the Almora/Nainital fix is right?**
Swapping restores smooth series for both districts. Almora stays ~80–105k and Nainital grows 590k → 840k. The
alternative would need Almora to grow 6× in one year and collapse 7× three years later. I logged it as an assumption.

**Q: Is the correlation significant?**
Borderline overall (p ≈ 0.05) and not at all without 2013. With 121 points and many confounders, I wouldn't claim
rainfall drives tourism; I'd claim extreme events do, which the event study shows much more clearly.

**Q: Why Spearman and not Pearson?**
Pearson measures linear association and is sensitive to outliers like a −93% year; Spearman uses ranks, so it is
robust to skew and outliers.

**Q: What would you do with more time?**
Difference-in-differences for Kedarnath with unaffected districts as controls; monthly data (monsoon vs. yatra
season); district-level landslide data (e.g. a national landslide inventory); sensitivity analysis on index weights.

**Q: Why is the record count small? The old README said 50,000+.**
It was wrong. The real data is 275 tourism rows, 182 rainfall rows and 9 landslide rows. Small, clean and honest
beats big and fake. (The "50,000+" and "25% faster decision-making" claims were removed.)

**Q: What did you personally do?** → Prepare this answer yourself (see the top of this guide).

---

## 7. Things NOT to say

- Not "50,000+ records", "Tableau dashboards" (there are none) or "improved decision-making speed by 25%".
- Not "rainfall causes tourism decline". Say "the 2013 extreme event caused a sharp, district-specific decline".
- Don't present the group project as solo work.
- Don't call the resilience index "the" resilience score. It's one transparent, assumption-dependent composite.
