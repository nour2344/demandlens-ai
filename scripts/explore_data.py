
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT_DIR / "data" / "raw" / "retail_sample.parquet"

df = pd.read_parquet(DATA_PATH)

print("\n===== DATASET OVERVIEW =====")
print("Shape:", df.shape)
print("Number of stores:", df["store_id"].nunique())
print("Number of products:", df["product_id"].nunique())
print("Store-product pairs:",
      df[["store_id", "product_id"]].drop_duplicates().shape[0])

print("\n===== DATE RANGE =====")
print("Start date:", df["dt"].min())
print("End date:", df["dt"].max())

print("\n===== MISSING VALUES =====")
print(df.isnull().sum())

print("\n===== DUPLICATE RECORDS =====")
print(df.duplicated(subset=["store_id", "product_id", "dt"]).sum())

print("\n===== STOCKOUT ANALYSIS =====")
stockouts = df[df["stock_hour6_22_cnt"] > 0]

print("Total records:", len(df))
print("Records with daytime stockouts:", len(stockouts))
print(f"Stockout rate: {len(stockouts) / len(df):.2%}")

print("\n===== STOCKOUT EXAMPLES =====")
columns = ["store_id", "product_id", "dt",
           "sale_amount", "stock_hour6_22_cnt"]

print(stockouts[columns].head(10).to_string(index=False))
