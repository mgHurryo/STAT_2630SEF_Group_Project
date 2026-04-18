# Module 03: ADS Code

Language: English / [中文](./03_ADS_Code_CN.md)

## Overview

ADS (Application Data Service) is the core module of this project for data analysis and result generation. It is responsible for transforming the comment data curated in the DWS layer into explainable, reportable, and visualized application-layer outputs. The module revolves around comment quality filtering, text preprocessing, sentiment analysis, topic classification, and the construction of standard ADS results, forming a complete closed-loop analysis pipeline.

The module ultimately delivers two core outputs:

1. Comment-level result table `ads_comment_theme_analysis`
2. Season-level overall evaluation table `ads_season_overall_evaluation`

## Directory Structure

```text
03_ADS_Code/
└── ADS_Colab_260406_2207.ipynb
```

The ADS layer is implemented as a Jupyter Notebook, running in a Google Colab-style environment and combining Spark, MongoDB, and external LLM APIs to complete the full analysis workflow.

## Pipeline Overview

```text
DWS Comment Data
    ↓
Step 1: Rule-based Pre-filtering and Deduplication   → dws_comment_rule_filtered
    ↓
Step 2: Multi-model Comment Filtering                → dws_comment_model_filtered
    ↓
Step 3: Text Preprocessing                           → dws_comment_preprocessed
    ↓
Step 4: Sentiment Analysis                           → dws_comment_sentiment_analysis
    ↓
Step 5: Topic Classification                         → dws_comment_topic_analysis
    ↓
Step 6: Result Merging                               → dws_comment_theme_analysis
    ↓
Step 7: ADS Comment-level Output                     → ads_comment_theme_analysis
    ↓
Step 8: ADS Season-level Aggregation                 → ads_season_overall_evaluation
```

## Technical Architecture

### Runtime Environment

| Item | Configuration |
|---|---|
| Python | `3.12+` |
| Spark | `4.0.2` |
| Scala | `2.13.16` |
| Database | MongoDB |
| Execution Environment | Google Colab-style environment |

### Key Dependencies

| Category | Dependencies |
|---|---|
| Core utilities | `os`, `re`, `json`, `time`, `threading`, `queue` |
| Data processing | `pandas` |
| Chinese text processing | `jieba`, `stopwords-zh`, `filter_stopwords`, `SnowNLP` |
| Keyword extraction | `KeyBERT`, `SentenceTransformer`, `CountVectorizer` |
| Model inference | `transformers`, `pipeline` |
| Concurrent execution | `ThreadPoolExecutor`, `as_completed` |
| Database | `pymongo`, `MongoClient` |
| Distributed processing | `pyspark.sql.SparkSession` |
| API calls | `requests` |

### Data Flow Path

`MongoDB -> Spark -> Pandas -> Spark -> MongoDB + CSV`

This architecture ensures both scalable batch read/write capability and flexible processing during the comment text analysis stage.

## Database and CSV Utility Layer

Before the main pipeline begins, the notebook builds a general-purpose utility layer to unify database read/write operations, CSV import/export, and Spark session management. This is an important foundation that allows the full ADS workflow to be reused reliably.

### Key Functions

| Function | Purpose |
|---|---|
| `connect_spark()` | Create a SparkSession and attach the MongoDB Connector |
| `ensure_spark_session()` | Support either SparkSession or Mongo URI input |
| `get_mongo_reader()` | Generate a MongoDB Reader |
| `get_mongo_writer()` | Generate a MongoDB Writer |
| `load_mongo_to_dataframe()` | Read a MongoDB collection and convert it to a DataFrame |
| `insert_dataframe_to_collection()` | Write results back to MongoDB |
| `export_dataframe_to_csv()` | Export a single CSV file |
| `export_all_collections_to_csv()` | Export all collections in batch |

### Value of the Utility Layer

This layer enables each stage of the pipeline to share the same input/output pattern, ensuring that the entire ADS module remains structurally consistent, operationally smooth, and complete in delivery.

## Stage-by-Stage Description

## Step 1: Rule-based Pre-filtering and Deduplication

This stage performs basic cleaning and rule-based deduplication for the raw comment data, including:

- removing empty comments and empty usernames
- trimming leading and trailing spaces and empty strings
- filtering comments made up only of symbols, only of numbers, or comments that are too short
- standardizing comment text and usernames
- deduplicating by three rules: same season and same user, same season and same content, and identical content across seasons

**Input:** `dws_douban_comment`  
**Output:** `dws_comment_rule_filtered`

Run result: out of the original `3999` comments, `3552` were retained after rule-based pre-filtering, with a retention rate of `88.82%`.

---

## Step 2: Multi-model Comment Filtering

This stage uses four text classification models collaboratively to determine whether a comment is suitable for entering the formal analysis workflow:

| Variable Name | Model | Function |
|---|---|---|
| `garbage` | `Titeiiko/OTIS-Official-Spam-Model` | preliminary screening for abnormal comments |
| `garbage2` | `textdetox/xlmr-large-toxicity-classifier-v2` | offensive comment detection |
| `garbage3` | `mrm8488/bert-tiny-finetuned-sms-spam-detection` | advertisement/spam detection |
| `garbage4` | `baptistejamin/xlm-roberta-large-spam_v4` | regular / advertisement / garbled-text classification |

The combined scoring formula is as follows:

```text
k2 = score2 if label2 == "LABEL_0" else 1 - score2
k3 = score3 if label3 == "LABEL_0" else 1 - score3
k4 = score4 if label4 == "regular" else 1 - score4

final_score = 0.2 * k2 + 0.35 * k3 + 0.45 * k4
```

After quality validation at this stage, comments are written into `dws_comment_model_filtered`. Run result: out of `3552` comments, `2499` were retained, with a retention rate of `70.35`.

---

## Step 3: Text Preprocessing

This stage converts comments into standardized text suitable for NLP analysis. The main processing includes:

- splitting text into sentences based on sentence-ending punctuation
- using `jieba` for Chinese word segmentation
- removing stopwords with `stopwords-zh`
- cleaning empty tokens and symbol-only tokens
- filtering sentences that are too short
- generating `processed_comment`

**Input:** `dws_comment_model_filtered`  
**Output:** `dws_comment_preprocessed`

Run result: `2499` comments were transformed into `2285` standardized analysis records after text preprocessing.

---

## Step 4: Sentiment Analysis

Sentiment analysis adopts a multi-model collaborative mechanism to generate keywords, sentiment probability distributions, and final sentiment labels for each comment.

### Models Used

| Capability | Model |
|---|---|
| Five-star sentiment model | `nlptown/bert-base-multilingual-uncased-sentiment` |
| Three-class sentiment model | `cardiffnlp/twitter-xlm-roberta-base-sentiment` |
| Keyword extraction | `KeyBERT` + `paraphrase-multilingual-MiniLM-L12-v2` |
| Auxiliary keyword extraction | `SnowNLP` |
| LLM re-review | `deepseek-chat` |

### Sentiment Decision Logic

- the five-star model is first mapped into a three-class sentiment distribution
- the three-class model directly outputs positive / neutral / negative distributions
- lightweight bias is applied based on common expressions in film and television reviews
- the two model outputs are merged with a `0.6 / 0.4` weighting
- conflicting comments are sent to the LLM for re-review
- negative comments go through a concurrent second-round re-review

**Input:** `dws_comment_preprocessed`  
**Output:** `dws_comment_sentiment_analysis`

The output table includes:

- comment keywords
- five-star model distributions and primary labels
- three-class model distributions and primary labels
- merged final sentiment distributions
- sentiment labels and decision sources
- LLM re-review results and final labels

This stage ultimately generated explainable sentiment analysis results for all `2285` comments.

---

## Step 5: Topic Classification

Topic classification assigns each comment to one of the following three topics:

- `Cast`
- `Plot`
- `Sentiment`

### Model Pool Design

Topic classification runs on a multi-model pool based on multiple API configurations, including DeepSeek, Qwen, Kimi, and MiniMax. Before formal execution, the notebook first performs smoke tests and concurrent stress tests, and then includes all models that pass the tests in the available model pool.

**Input:** `dws_comment_preprocessed`  
**Output:** `dws_comment_topic_analysis`

Run result: all `2285` comments completed topic classification, and the `used_model` field was retained to track which model was actually used.

---

## Step 6: Merge Sentiment and Topic Results

This stage merges the sentiment analysis results with the topic classification results into a complete comment-level analysis table.

**Input:**

- `dws_comment_sentiment_analysis`
- `dws_comment_topic_analysis`

**Output:** `dws_comment_theme_analysis`

The merged result table preserves:

- basic comment information
- keywords
- five-star model results
- three-class model results
- merged sentiment results
- topic classification results
- LLM explanation information

Run result: after merging, a total of `2285` complete comment analysis records were produced.

---

## Step 7: Generate the ADS Comment-level Result Table

This stage compresses the complete comment analysis result into the ADS-standard five-field structure:

- `season`
- `comment`
- `keyword`
- `sentiment_association`
- `topic_category`

**Input:** `dws_comment_theme_analysis`  
**Output:** `ads_comment_theme_analysis`

Run result: `2285` ADS comment-level results were generated.

---

## Step 8: Generate the ADS Season-level Overall Evaluation Table

This stage aggregates and merges the comment-level results with the season rating table to generate season-level overall evaluation results.

**Input:**

- `ads_comment_theme_analysis`
- `dws_season_rating_comparison`

**Output:** `ads_season_overall_evaluation`

The result table includes the following fields:

- `season_id`
- `df_douban_rating`
- `imdb_rating`
- `rating_difference`
- `positive_comment_cnt`
- `negative_comment_cnt`
- `netral_common_cnt`
- `total_common_cnt`

Run result: a total of `10` season-level overall evaluation records were generated.

## Final Deliverables

The notebook ultimately exports the raw tables, intermediate tables, analysis tables, and result tables as CSV files, for a total of 10 files, including:

- `dws_douban_comment.csv`
- `dws_comment_rule_filtered.csv`
- `dws_comment_model_filtered.csv`
- `dws_comment_preprocessed.csv`
- `dws_comment_sentiment_analysis.csv`
- `dws_comment_topic_analysis.csv`
- `dws_comment_theme_analysis.csv`
- `ads_comment_theme_analysis.csv`
- `dws_season_rating_comparison.csv`
- `ads_season_overall_evaluation.csv`
