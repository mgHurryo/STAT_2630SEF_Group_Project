# Module 04: Visualization

Lauguage: English / [中文](./04_Visualization_CN.md)

## Overview

This module presents the analysis results from the ADS layer as interactive charts and dashboards, enabling intuitive exploration of the data.

## Directory Structure

```
04_Visualization/
└── mgHurryo.pbix    # Power BI Desktop file
```

The dashboard is built in **Microsoft Power BI** and distributed as a `.pbix` file.

## Dashboard Contents

The Power BI dashboard (`mgHurryo.pbix`) visualizes the ADS layer output, covering:

- **Season rating comparison:** Douban vs IMDB ratings for each season
- **Sentiment distribution:** Proportion of positive, negative, and neutral comments
- **Topic breakdown:** Distribution of comments across 演员 (Acting), 剧情 (Plot), and 情怀 (Nostalgia)
- **Keyword cloud:** Most frequently mentioned keywords in the comment corpus
- **Trend analysis:** Changes in sentiment and ratings across seasons

## Usage

1. Install **Power BI Desktop** (free download: https://powerbi.microsoft.com/desktop/)
2. Open `04_Visualization/mgHurryo.pbix`
3. The dashboard loads with embedded data

## Data Source

The Power BI file embeds data from the ADS output tables:
- `ads_season_overall_evaluation.csv` — Season-level summary
- `ads_comment_theme_analysis.csv` — Comment-level detailed analysis

To refresh the data source after underlying data updates:
1. Navigate to **Home → Transform data**
2. Update file paths to point to the latest CSV files
3. Click **Refresh** to reload

## Notes

- The `.pbix` file is a **binary file** and cannot be viewed or edited in a text editor
- Power BI Desktop is required to open and modify the dashboard
- The file can be published to Power BI Service (cloud) for online sharing
- Power BI Desktop (free) is sufficient for viewing the dashboard

---

[Return to English README](../README.md) / [返回中文 README](README_CN.md)

---
