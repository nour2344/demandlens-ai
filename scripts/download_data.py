
from pathlib import Path

import pandas as pd
from datasets import load_dataset


DATASET_NAME = "Dingdong-Inc/FreshRetailNet-50K"
SAMPLE_SIZE = 10_000

ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT_DIR / "data" / "raw" / "retail_sample.parquet"


def download_data():
    print("Loading FreshRetailNet-50K...")

    dataset = load_dataset(
        DATASET_NAME,
        split="train",
        streaming=True
    )

    records = list(dataset.take(SAMPLE_SIZE))
    df = pd.DataFrame(records)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUTPUT_PATH, index=False)

    print("\nDataset successfully saved!")
    print(f"Shape: {df.shape}")
    print(f"Saved to: {OUTPUT_PATH}")

    print("\nFirst 5 rows:")
    print(df.head())

    print("\nColumn names:")
    print(df.columns.tolist())


if __name__ == "__main__":
    download_data()
