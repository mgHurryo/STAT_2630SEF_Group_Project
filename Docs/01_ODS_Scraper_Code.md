# Module 01: ODS Scraper Code

Lauguage: English / [中文](./01_ODS_Scraper_Code_CN.md)

## Overview

This module serves as the data collection layer of the project. It uses Scrapy to extract raw data from Douban — a Chinese review platform — including season-level ratings and user comments for the TV series "Friends".

## Directory Structure

```
01_ODS_Scraper_Code/
├── comment/               # Comment scraper (Scrapy project)
│   ├── comment/
│   │   ├── spiders/
│   │   │   └── douban_comment.py   # Comment spider implementation
│   │   ├── items.py                # Data structure definitions
│   │   ├── pipelines.py            # Data processing pipeline
│   │   ├── middlewares.py          # Request/response middleware
│   │   └── settings.py             # Spider configuration
│   └── scrapy.cfg                  # Scrapy project configuration
├── rating/                # Rating scraper (Scrapy project)
│   ├── rating/
│   │   ├── spiders/
│   │   │   └── rate.py             # Rating spider implementation
│   │   ├── items.py                # Data structure definitions
│   │   ├── pipelines.py            # Data processing pipeline
│   │   ├── middlewares.py          # Request/response middleware
│   │   └── settings.py             # Spider configuration
│   └── scrapy.cfg                  # Scrapy project configuration
└── run_scraper.py         # Unified runner script
```

## Scrapers

### Rating Scraper (`rating/`)

Extracts season-level ratings from Douban search results for "Friends" (老友记).

**Workflow:**
1. Queries Douban search for "老友记"
2. Parses the first 10 results, each corresponding to a season
3. Extracts the following fields per result:
   - **Season name** (e.g., "老友记 第一季")
   - **Rating score** (e.g., 9.7)
   - **Number of raters** (e.g., 200,000)
4. Outputs results as JSON

**Key file:** `rating/rating/spiders/rate.py`

### Comment Scraper (`comment/`)

Extracts user comments for "Friends" Season 1 from Douban.

**Workflow:**
1. Accesses the Douban page for Friends Season 1 (subject ID: 3286552)
2. Parses 20 comments per page across 20 pages (~400 comments total)
3. Extracts the following fields per comment:
   - **Comment ID** (auto-generated, starting from 3600)
   - **Season** (set to 10)
   - **Comment content** (original text)
   - **Username** (author)
4. Outputs results as JSON

**Key file:** `comment/comment/spiders/douban_comment.py`

## Anti-Detection Measures

Douban employs mechanisms to limit automated access. The scrapers incorporate the following measures:

- **User-Agent rotation:** Identifies as a standard Safari browser
- **Cookie authentication:** Uses valid Douban session cookies to appear as an authenticated user
- **Download delay:** Enforces a 3-second interval between requests to avoid excessive load
- **Auto-throttle:** Dynamically adjusts request speed based on server response times
- **HTTP caching:** Caches previously fetched pages to prevent redundant requests

## Runner Script (`run_scraper.py`)

The entry point that executes both scrapers sequentially:

1. Runs the **rating scraper** → outputs to `data/ODS_Resource_Data/rating.json`
2. Runs the **comment scraper** → outputs to `data/ODS_Resource_Data/comment.json`
3. Reports execution status for each scraper

## Output Data

| File | Content | Format |
|------|---------|--------|
| `data/ODS_Resource_Data/rating.json` | Season ratings from Douban | JSON array |
| `data/ODS_Resource_Data/comment.json` | User comments from Douban | JSON array |

## Usage

```bash
cd 01_ODS_Scraper_Code
python run_scraper.py
```

## Notes

- The comment scraper targets **Season 1 only** (subject ID: 3286552). Modify the URL to scrape other seasons
- The scraper is limited to **20 pages** (400 comments). Adjust the `self.page <= 400` condition to increase the page count

---

[Return to English README](../README.md) / [返回中文 README](README_CN.md)

---
