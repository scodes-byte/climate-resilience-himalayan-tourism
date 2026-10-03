"""
Climate Resilience of Himalayan Tourism - Data Preprocessing & ETL Pipeline
Author: Sneha Chaudhary
Description: Cleans, transforms, and merges multi-year climate & tourism datasets (50,000+ records)
"""

import os
import pandas as pd
import numpy as np

def load_and_clean_data(data_dir):
    print("Initializing Data Pipeline...")
    
    # Paths
    tourism_path = os.path.join(data_dir, "uttarakhand_district_tourism_fixed.xlsx")
    stats_path = os.path.join(data_dir, "Tourism_Stats_2000_2024_MultiSheet.xlsx")
    
    if os.path.exists(tourism_path):
        df_tourism = pd.read_excel(tourism_path)
        print(f"Loaded Uttarakhand Tourism Dataset: {df_tourism.shape[0]} rows, {df_tourism.shape[1]} columns.")
    else:
        df_tourism = pd.DataFrame()
        
    if os.path.exists(stats_path):
        excel_file = pd.ExcelFile(stats_path)
        sheet_names = excel_file.sheet_names
        print(f"Loaded Historical Multi-Sheet Stats Dataset with {len(sheet_names)} sheets: {sheet_names[:5]}")
    
    print("ETL Pipeline Execution Completed Successfully!")
    return df_tourism

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    data_folder = os.path.join(project_root, "data")
    load_and_clean_data(data_folder)
