# Module 02: DWS Code

Lauguage: English / [中文](./02_DWS_Code_CN.md)

## Overview

This module serves as the data processing layer of the project. It takes the raw data collected by the ODS layer, cleans and structures it, and integrates external data sources (IMDB ratings) to produce standardized tables ready for downstream analysis.

## Directory Structure

```
02_DWS_Code/
└── dws层生成.ipynb    # Jupyter Notebook (runs on Google Colab)
```

The entire DWS layer is implemented as a single Jupyter Notebook, designed to run on Google Colab.

## Processing Tasks

### Task 1: Season Rating Comparison Table

**Input:**
- Douban season ratings (from MongoDB `ods_data.ods_douban_season_rating`)
- IMDB episode ratings (from MongoDB `ods_data.ods_friends_episodes_v3`)

**Processing:**
1. Connects to MongoDB and retrieves both rating datasets
2. Calculates the average IMDB rating per season from episode-level data
3. Joins Douban ratings with IMDB ratings by season
4. Computes the **rating difference** (Douban score minus IMDB score)

**Output table (`dws_season_rating_comparison`):**

| season | df_douban_rating | imdb_rating | rating_difference |
|--------|-----------------|-------------|-------------------|
| 1      | 9.7             | 8.3         | 1.4               |
| 2      | 9.8             | 8.5         | 1.3               |
| 3      | 9.7             | 8.4         | 1.3               |
| ...    | ...             | ...         | ...               |

The rating difference reveals that Douban users consistently rate "Friends" approximately 1.2–1.4 points higher than IMDB users, which is a notable observation for cross-cultural audience analysis.

### Task 2: Douban Comment Table

**Input:**
- Raw Douban comments (from MongoDB `ods_data.ods_douban_comment`)

**Processing:**
1. Retrieves all raw comment data from MongoDB
2. Renames and standardizes columns:
   - `id` → `user_id`
   - `name` → `user_name`
   - `season` and `comment` retained as-is
3. Sorts by season number

**Output table (`dws_douban_comment`):**

| user_id | season | user_name | comment |
|---------|--------|-----------|---------|
| 199     | 1      | 猫猫eko   | 这个就不用我多说了吧。。。不笑除非你没长嘴。 |
| 350     | 1      | 日光瀑布  | 我的大学时光 |
| ...     | ...    | ...       | ...     |

## Technologies

| Technology | Purpose |
|------------|---------|
| **DuckDB** | Fast SQL queries on local data (lightweight analytical database) |
| **Pandas** | Data manipulation and table operations |
| **PyMongo** | MongoDB connection and data I/O |

## Data Flow

```
MongoDB (ODS raw data)
    ↓
DWS Notebook (DuckDB SQL + Pandas)
    ↓
MongoDB (DWS processed data)
    - dws_season_rating_comparison
    - dws_douban_comment
```

## Usage

1. Open `02_DWS_Code/dws层生成.ipynb` in Google Colab or Jupyter Notebook
2. Install dependencies (the notebook handles this automatically via `!pip install pymongo`)
3. Execute all cells in sequence

---

[Return to English README](../README.md) / [返回中文 README](README_CN.md)

---
