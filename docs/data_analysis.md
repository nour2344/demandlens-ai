
# Exploratory Data Analysis

## Data Source

FreshRetailNet-50K, published by Dingdong Inc.

https://huggingface.co/datasets/Dingdong-Inc/FreshRetailNet-50K

## Sample Overview

| Metric | Value |
|---|---:|
| Records | 10,000 |
| Features | 19 |
| Stores | 2 |
| Unique products | 103 |
| Store-product pairs | 112 |
| Historical coverage | 90 days |
| Start date | 2024-03-28 |
| End date | 2024-06-25 |
| Missing values | 0 |
| Duplicate records | 0 |
| Daytime stockout records | 4,806 |
| Daytime stockout rate | 48.06% |

## Key Findings

- No column-level missing values or duplicate records were detected.
- Nearly half of the sampled daily records contain daytime stockouts.
- Hourly sales and stock availability enable stockout investigations.
- Historical observations support comparable-period demand estimation.

## Limitations

- The sample consists of the first 10,000 training records.
- The sample is not representative of the entire dataset.
- Sales values are normalized.
- Actual unmet demand during stockouts is unobserved.
- Hourly array integrity requires further validation.
