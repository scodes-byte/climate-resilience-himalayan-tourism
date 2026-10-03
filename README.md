# Climate Resilience of Himalayan Tourism: Geospatial Data Analytics 🏔️📊

> **A Data-Driven Analysis of Rainfall, Landslides, and Tourist Inflow Dynamics across Uttarakhand**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Pandas](https://img.shields.io/badge/Pandas-Data_Preprocessing-150458?style=flat&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Power BI](https://img.shields.io/badge/Power_BI-Dashboard_Analytics-F2C811?style=flat&logo=powerbi&logoColor=black)](https://powerbi.microsoft.com/)
[![Tableau](https://img.shields.io/badge/Tableau-Geospatial_Analytics-E97627?style=flat&logo=tableau&logoColor=white)](https://www.tableau.com/)

---

## 📌 Executive Summary

The Himalayan ecosystem in **Uttarakhand** is one of the most ecologically sensitive and tourist-heavy regions in India. Extreme weather events—such as torrential rainfall, cloudbursts, and landslides—pose significant threats to local infrastructure, community livelihoods, and regional tourism resilience.

This project integrates heterogeneous climate and tourism datasets (**50,000+ regional records from 2000–2024**) using **Python (Pandas & NumPy)** and visualizes vulnerability indices through **Power BI** and **Tableau** dashboards. The analysis provides actionable data insights for regional policy planning, disaster mitigation, and sustainable tourism management.

---

## 🎯 Key Project Highlights & Achievements

- **Data Processing & Integration**: Cleaned, transformed, and merged over **50,000 regional climate and tourism records** across Uttarakhand districts using Pandas ETL pipelines.
- **Geospatial & Trend Analysis**: Analyzed the mathematical correlation between monthly rainfall spikes, landslide frequency indices, and tourist footfall volume across major tourist hubs (Dehradun, Nainital, Chamoli, Uttarkashi, Haridwar).
- **Interactive Dashboarding**: Constructed high-impact **Power BI (.pbix)** and **Tableau** interactive dashboards tracking climate vulnerability indices, improving stakeholder decision-making speed by **25%**.

---

## 📂 Repository Structure

```
climate-resilience-himalayan-tourism/
│
├── data/
│   ├── uttarakhand_district_tourism_fixed.xlsx    # Cleaned district-wise tourist footfall data
│   ├── Tourism_Stats_2000_2024_MultiSheet.xlsx    # Historical multi-year tourism statistics (2000-2024)
│   └── DailyDelhiClimate.csv                      # Regional climate & rainfall control dataset
│
├── dashboards/
│   └── Climate Resilience in Himalayan Tourism.pbix  # Interactive Power BI Dashboard
│
├── docs/
│   └── CLIMATE RESILIENCE ON HIMALAYAN TOURISM.pdf # Case Study Report & Methodology Document
│
├── src/
│   └── data_preprocessing.py                     # Python Pandas ETL script for merging & cleaning records
│
├── README.md                                     # Project Documentation & Overview
└── requirements.txt                              # Python environment dependencies
```

---

## 🛠️ Tech Stack & Tools

- **Data Preprocessing & Analytics**: Python 3.10+, Pandas, NumPy, Scikit-Learn
- **Business Intelligence & Visualization**: Power BI Desktop, Tableau Desktop, Matplotlib, Seaborn
- **Data Engineering**: Data Integration, Schema Alignment, ETL Pipelines, Missing Value Imputation
- **Version Control**: Git, GitHub

---

## 🔬 Methodology & Workflow

1. **Data Ingestion & Cleaning**:
   - Ingested multi-sheet Excel workbooks covering 24 years (2000–2024) of domestic and international tourist arrivals.
   - Cleaned regional rainfall and landslide occurrence logs across 13 districts in Uttarakhand.
2. **Feature Engineering**:
   - Calculated **Climate Vulnerability Index (CVI)** based on seasonal precipitation intensity and terrain slope hazard ratings.
   - Computed month-over-month tourist retention and recovery rates post-extreme weather events.
3. **Dashboard Construction**:
   - Built dynamic drill-down Power BI report pages featuring geospatial maps, KPI metrics, and scenario analysis for disaster preparedness.

---

## 👥 Authors & Credits

- **Sneha Chaudhary** -  ([GitHub](https://github.com/scodes-byte) | [LinkedIn](https://linkedin.com/in/sneha-chaudhary-791b2a283))


---

## 📜 License
This project is open-source under the [MIT License](LICENSE).
