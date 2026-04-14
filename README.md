# STAT_2630SEF_Group_Project

Language: English / [中文](Docs/README_CN.md)

**Topic:** Sentiment Analysis-Based Study on Chinese Audiences' Acceptance of "Friends"

**Environment:** `Python 3.12+`

---

## Project Overview

This project constructs a data pipeline following a data warehouse architecture (ODS → DWS → ADS) to collect, process, analyze, and visualize Douban comments and ratings for the TV series "Friends" (老友记). The pipeline covers the full workflow from web scraping through NLP-based sentiment analysis to interactive visualization.

## Project Structure

```
STAT_2630SEF_Group_Project/
├── 01_ODS_Scraper_Code/       # Data Scraping Layer (Operational Data Store)
├── 02_DWS_Code/               # Data Warehouse Service Layer
├── 03_ADS_Code/               # Application Data Service Layer
├── 04_Visualization/          # Power BI Dashboard
├── data/                      # Data Storage (ODS, DWS, ADS)
├── Docs/                      # Documentation
└── README.md
```

## Module Documentation

Detailed documentation for each module is available in the `Docs/` folder:

| Module | Description | Documentation |
|--------|-------------|---------------|
| **01 ODS Scraper** | Web scraping from Douban | [English](Docs/01_ODS_Scraper_Code.md) / [中文](Docs/01_ODS_Scraper_Code_CN.md) |
| **02 DWS** | Data cleaning and aggregation | [English](Docs/02_DWS_Code.md) / [中文](Docs/02_DWS_Code_CN.md) |
| **03 ADS** | NLP analysis and sentiment classification | [English](Docs/03_ADS_Code.md) / [中文](Docs/03_ADS_Code_CN.md) |
| **04 Visualization** | Power BI dashboard | [English](Docs/04_Visualization.md) / [中文](Docs/04_Visualization_CN.md) |

## Data Pipeline Architecture

### 1. ODS Layer (Data Scraping)

Located in `01_ODS_Scraper_Code/`. This layer uses Scrapy to collect raw data from Douban:

- **Rating Scraper** (`rating/`): Extracts season-level ratings from Douban search results
- **Comment Scraper** (`comment/`): Extracts user comments for "Friends" Season 1 (subject ID: 3286552), paginating through 20 pages (~400 comments)
- **Runner** (`run_scraper.py`): Orchestrates both scrapers sequentially, outputs to `data/ODS_Resource_Data/`

**Output:** `rating.json`, `comment.json`

**Detailed Doc:** [English](Docs/01_ODS_Scraper_Code.md) / [中文](Docs/01_ODS_Scraper_Code_CN.md)

### 2. DWS Layer (Data Processing)

Located in `02_DWS_Code/`. This layer cleans and aggregates raw data:

- Generates `dws_season_rating_comparison` table comparing Douban vs IMDB ratings per season
- Cleans and standardizes the raw comment data into `dws_douban_comment`
- Uses DuckDB, Pandas, and MongoDB for data processing

**Output:** `dws_season_rating_comparison.csv`, `dws_douban_comment.csv`

**Detailed Doc:** [English](Docs/02_DWS_Code.md) / [中文](Docs/02_DWS_Code_CN.md)

### 3. ADS Layer (Data Analysis)

Located in `03_ADS_Code/`. This layer performs the core analytical work:

- **Data Filtering:** Two-stage filtering using regex rules followed by ensemble AI models for spam and toxicity detection
- **Text Preprocessing:** Jieba Chinese word segmentation with stopword filtering
- **Sentiment Analysis:** Multi-model committee (5-star and 3-value classifiers) with LLM-based tiebreaking for ambiguous cases
- **Topic Classification:** LLM API-based categorization into 演员 (Acting), 剧情 (Plot), and 情怀 (Nostalgia)
- **Concurrent Execution:** Multi-threaded processing across multiple LLM endpoints for throughput and fault tolerance

**Output:**
- `ads_season_overall_evaluation.csv` — Per-season summary with ratings and sentiment distribution
- `ads_comment_theme_analysis.csv` — Per-comment analysis with keywords, sentiment labels, and topic categories

**Detailed Doc:** [English](Docs/03_ADS_Code.md) / [中文](Docs/03_ADS_Code_CN.md)

### 4. Visualization

Located in `04_Visualization/`. Contains a Power BI dashboard (`mgHurryo.pbix`) for interactive exploration of the analysis results.

**Detailed Doc:** [English](Docs/04_Visualization.md) / [中文](Docs/04_Visualization_CN.md)

## Data Directory Structure

```
data/
├── ODS_Resource_Data/         # Raw scraped data (JSON)
└── ADS_Resource_Data/
    ├── 1_Raw/                 # DWS-level inputs
    ├── 2_Intermediate/        # Intermediate processing results
    ├── 3_Processed/           # Final ADS output tables
    └── 4_Backup/              # Data backups
```

## Key Technologies

- **Web Scraping:** Scrapy
- **Data Processing:** DuckDB, Pandas, PyMongo, PySpark
- **NLP:** Jieba, KeyBERT, SnowNLP, Hugging Face Transformers
- **LLM APIs:** DeepSeek, Qwen, Kimi, MiniMax
- **Visualization:** Power BI
- **Development:** Google Colab (GPU/T4), Jupyter Notebook

## Usage

1. **Run Scrapers:**
   ```bash
   cd 01_ODS_Scraper_Code
   python run_scraper.py
   ```

2. **Process DWS Layer:**
   Open `02_DWS_Code/dws层生成.ipynb` in Jupyter/Colab and run all cells

3. **Run ADS Analysis:**
   Open `03_ADS_Code/ADS_Colab_260406_2207.ipynb` in Jupyter/Colab and run all cells

4. **View Visualization:**
   Open `04_Visualization/mgHurryo.pbix` in Power BI Desktop
