# Module 03: ADS Code

Lauguage: English / [中文](./03_ADS_Code_CN.md)

## Overview

This module is the analytical core of the project. ADS stands for **Application Data Service**. It takes the cleaned data from the DWS layer and applies natural language processing (NLP) and machine learning techniques to extract sentiment, topics, and keywords from Douban comments.

## Directory Structure

```
03_ADS_Code/
└── ADS_Colab_XXXXXX_XXXX.ipynb    # Latest version (use this one)
```

The ADS layer is implemented as a Jupyter Notebook designed to run on **Google Colab with GPU support** (T4), as it executes computationally intensive AI models.

## Pipeline Overview

The analysis pipeline consists of seven stages:

```
DWS Comment Data
    ↓
Step 1: Regex Pre-screening    → dws_comment_rule_filtered
    ↓
Step 2: Model Fine-filtering   → dws_comment_model_filtered
    ↓
Step 3: Text Preprocessing     → dws_comment_preprocessed
    ↓
Step 4: Sentiment Analysis     → dws_comment_sentiment_analysis
    ↓
Step 5: Topic Classification   → dws_comment_topic_analysis
    ↓
Step 6: Merge Results          → dws_comment_theme_analysis
    ↓
Step 7: ADS Output             → ads_comment_theme_analysis + ads_season_overall_evaluation
```

---

## Step 1: Regex Pre-screening

A rule-based filter that removes low-quality comments before applying AI models, reducing computational cost.

**Source collection:** `dws_douban_comment`

### Implementation Details

The pipeline chains the following functions in sequence:

1. **Null/blank removal:** `remove_null_comments()` drops NaN rows; `strip_comment_whitespace()` strips leading/trailing spaces; `remove_blank_comments()` drops empty strings
2. **Normalization:** `normalize_comment_text()` removes all internal whitespace via `re.sub(r"\s+", "", text)`; `normalize_username_text()` compresses consecutive spaces to single space
3. **Content filtering:**
   - `is_all_symbol()` — uses `re.search(r"[\u4e00-\u9fffA-Za-z0-9]", text)` to detect pure-symbol comments
   - `is_all_number()` — uses `re.fullmatch(r"\d+", text)` to detect pure-number comments
   - `remove_short_comments()` — filters comments with `comment_clean` length < 2
4. **Deduplication (3 rules):**
   - **Rule 1 — Same user, same season:** `deduplicate_same_season_same_user()` groups by `(season, user_name_clean)`, keeps the longest comment; ties broken by later row order
   - **Rule 2 — Different users, same season, same content:** `deduplicate_same_season_same_comment()` drops duplicates on `(season, comment_clean)`
   - **Rule 3 — Cross-season same content:** `remove_cross_season_same_comments()` deletes ALL occurrences if the same `comment_clean` appears in more than one distinct season

**Output:** `dws_comment_rule_filtered`
- **Path:** `data/ADS_Resource_Data/2_Intermediate/dws_comment_rule_filtered.csv`
- **Columns:** `season`, `user_name`, `comment`

---

## Step 2: Model Fine-filtering

Uses **four AI models** to detect and remove spam, advertisements, gibberish, and toxic content.

**Source collection:** `dws_comment_rule_filtered`

### Models

| Variable | Model ID | Purpose | Labels |
|----------|----------|---------|--------|
| `garbage` | `Titeiiko/OTIS-Official-Spam-Model` | Spam pre-screen | LABEL_0=GARBAGE, LABEL_1=REGULAR |
| `garbage2` | `textdetox/xlmr-large-toxicity-classifier-v2` | Toxicity detection | LABEL_0=REGULAR, LABEL_1=ABUSE |
| `garbage3` | `mrm8488/bert-tiny-finetuned-sms-spam-detection` | Ad/spam detection | LABEL_0=REGULAR, LABEL_1=SPAM |
| `garbage4` | `baptistejamin/xlm-roberta-large-spam_v4` | Multi-class spam | spam, regular, gibberish |

### Scoring Formula

Each model's output is converted to a "keep tendency score":

```
k2 = score2  if label2 == "LABEL_0"  else  1 - score2
k3 = score3  if label3 == "LABEL_0"  else  1 - score3
k4 = score4  if label4 == "regular"  else  1 - score4

final_score = 0.2 * k2 + 0.35 * k3 + 0.45 * k4
```

### Veto Mechanism

If Model 1 flags the comment as garbage (LABEL_0), the final score is forced to 0 regardless of other models' scores.

### Decision

Comments with `final_score >= 0.6` are retained; the rest are discarded. Models are called in batches of 32 for efficiency.

**Output:** `dws_comment_model_filtered`
- **Path:** `data/ADS_Resource_Data/2_Intermediate/dws_comment_model_filtered.csv`
- **Columns:** `season`, `user_name`, `comment` (scoring columns dropped after filtering)

---

## Step 3: Text Preprocessing

Prepares comment text for NLP analysis through sentence splitting, tokenization, and noise removal.

**Source collection:** `dws_comment_model_filtered`

### Implementation Details

1. **Sentence splitting:** `split_sentences()` uses `re.split(r'[。！？!?；;…]+|\.(?=\s|$)', text)` to split on sentence-ending punctuation. Commas are preserved within sentences.
2. **Tokenization:** Each sentence is tokenized with `jieba.cut()`, then passed through `filter_stopwords()` from the `stopwords-zh` library.
3. **Token cleaning:** `clean_tokens()` removes blank tokens and tokens matching `re.fullmatch(r'[\W_]+', token)` (pure non-word characters).
4. **Short sentence filtering:** Sentences with fewer than 2 valid tokens after cleaning are discarded.
5. **Reconstruction:** Valid processed sentences are joined with `"."` as separator.

**Output:** `dws_comment_preprocessed`
- **Path:** `data/ADS_Resource_Data/2_Intermediate/dws_comment_preprocessed.csv`
- **Columns:** `season`, `comment`, `processed_comment`

---

## Step 4: Sentiment Analysis

Classifies each comment as positive, negative, or neutral using a multi-model ensemble with LLM-based arbitration.

**Source collection:** `dws_comment_preprocessed`

### Models

| Component | Model ID | Purpose |
|-----------|----------|---------|
| 5-Star Model | `nlptown/bert-base-multilingual-uncased-sentiment` | Rates text on a 1–5 star scale |
| 3-Value Model | `cardiffnlp/twitter-xlm-roberta-base-sentiment` | Classifies as positive/neutral/negative |
| Keyword Extractor | KeyBERT + `paraphrase-multilingual-MiniLM-L12-v2` | Semantic keyword extraction |
| LLM Reviewer | DeepSeek / Qwen / Kimi (via API) | Resolves ambiguous cases and negative review |

### Score Conversion

**5-Star → Sentiment Distribution:**
- Star 1 → `negative += score`
- Star 2 → `negative += score * 0.7`, `neutral += score * 0.3`
- Star 3 → `neutral += score`
- Star 4 → `positive += score * 0.7`, `neutral += score * 0.3`
- Star 5 → `positive += score`

Scores are then normalized to sum to 1.0.

**3-Value → Distribution:** Direct mapping (label_0 → negative, label_1 → neutral, label_2 → positive), then normalized.

### Domain Phrase Bias

Predefined regex patterns (`positive_patterns`, `negative_patterns`) are matched against the original comment. If a positive pattern matches (without a negative one), `+0.08` is added to the positive score in both distributions; vice versa for negative patterns. Distributions are re-normalized after bias application.

### Decision Logic (4 Branches)

| Condition | Action |
|-----------|--------|
| Both models uncertain (`star_top_score <= 0.35` AND `tri_top_score <= 0.35`) | Force result to `neutral` (1.0) |
| Strong disagreement (one predicts positive, the other negative) | Invoke LLM; use LLM label as 1.0 one-hot |
| Different labels with large confidence gap (`abs(star_top_score - tri_top_score) >= 0.25`) | Invoke LLM; use LLM label as 1.0 one-hot |
| Normal case | Weighted fusion: `final = 0.6 * star_dist + 0.4 * tri_dist`, select argmax |

### Directional Protection

After weighted fusion, a safety check is applied:
- If neither model detected "negative" but the fused result is "negative" → remove "negative" and re-normalize over {neutral, positive}
- Same logic applies if neither detected "positive" but fusion yields "positive"

### LLM Negative Review

All comments labeled "negative" undergo an additional LLM review via `ThreadPoolExecutor` (multi-threaded). If the LLM reclassifies the comment as neutral or positive, the label is updated; otherwise it remains negative.

### Keyword Extraction (`extract_one_keyword`)

1. Attempt KeyBERT extraction with `keyphrase_ngram_range=(1, 2)`, `top_n=3` — take first valid keyword
2. Tokenize with jieba, filter to tokens of 2–8 characters (no spaces, no pure symbols, no pure digits)
3. Attempt SnowNLP keyword extraction on cleaned tokens
4. Fallback: return first cleaned token, or empty string

### Sentence-Level Processing

Comments are split into sentences (max 120 chars per chunk). Each sentence is analyzed independently, and results are weighted by sentence length ratio (`sent_len / total_len`).

**Output:** `dws_comment_sentiment_analysis`
- **Path:** `data/ADS_Resource_Data/2_Intermediate/dws_comment_sentiment_analysis.csv`
- **Key columns:** `season`, `comment`, `keyword`, `star_negative/neutral/positive`, `tri_negative/neutral/positive`, `final_negative/neutral/positive`, `sentiment_association`, `decision_type`, `llm_label`, `llm_reason`, `final_label_after_llm`

---

## Step 5: Topic Classification

Categorizes each comment into one of three topics: **演员 (Acting)**, **剧情 (Plot)**, or **情怀 (Nostalgia)**.

**Source collection:** `dws_comment_preprocessed`

### LLM Model Pool

Multiple LLM APIs are configured with individual settings:

| Model | Endpoint | Thread Workers |
|-------|----------|----------------|
| `deepseek-chat` | api.deepseek.com | 20 |
| `deepseek-v3.2-exp` | dashscope.aliyuncs.com | 10 |
| `kimi-k2.5` | dashscope.aliyuncs.com | 8 |
| `MiniMax-M2.5` | dashscope.aliyuncs.com | 8 |
| `deepseek-v3.1` | dashscope.aliyuncs.com | 8 |
| `qwen-turbo-latest` | dashscope.aliyuncs.com | 8 |
| `qwen-turbo` | dashscope.aliyuncs.com | 8 |

Each model has `timeout=60s` and `max_retries=3`.

### Model Evaluation

Before production use, models undergo a two-stage evaluation:

1. **Smoke test:** A single call with a fixed test comment verifies connectivity and response validity. Failed models are eliminated immediately.
2. **Pressure test:** Models that pass the smoke test receive concurrent requests (`thread_workers * 2` rounds) across 5 rotating test comments. Only models with a success rate ≥ 80% enter the production pool (`AVAILABLE_TOPIC_MODELS`).

### Concurrent Processing Architecture

Each available model is wrapped in a `TopicModelWorker` with its own `ThreadPoolExecutor`:

- **Task dispatching:** Comments are distributed round-robin (`idx % len(model_workers)`) to workers via thread-safe `queue.Queue()`
- **Worker execution:** Each worker thread runs a `worker_loop()` that continuously pulls tasks from the queue
- **Failover:** If a model fails on a comment, it automatically retries with the next available model in the pool. If all models fail, the comment is labeled "其他" (Other)
- **Retry:** Each API call uses exponential backoff: `time.sleep(1.5 * (attempt + 1))`
- **Result synchronization:** Results are stored in a shared `result_dict` protected by `threading.Lock()`. `task_queue.join()` ensures all tasks complete before aggregation

### LLM Prompt

The prompt instructs the model to classify the comment into one of the candidate labels and return JSON in the format `{"topic_category": "label", "reason": "explanation"}`. A regex fallback parser handles non-standard JSON responses.

**Output:** `dws_comment_topic_analysis`
- **Path:** `data/ADS_Resource_Data/2_Intermediate/dws_comment_topic_analysis.csv`
- **Columns:** `season`, `comment`, `topic_category`, `llm_topic_reason`, `used_model`

---

## Step 6: Merge Sentiment and Topic Results

Combines sentiment analysis and topic classification into a single comprehensive table.

**Source collections:** `dws_comment_sentiment_analysis` + `dws_comment_topic_analysis`

### Implementation

1. The topic table is deduplicated on `(season, comment)`, keeping the last entry
2. A left join is performed: `sentiment_df.merge(topic_df[[season, comment, topic_category]], on=[season, comment], how="left")`
3. Unmatched topic values are filled with "其他" (Other)
4. The merged table retains all sentiment scores, final labels, decision types, and topic categories (25 fields total)

**Output:** `dws_comment_theme_analysis`
- **Path:** `data/ADS_Resource_Data/2_Intermediate/dws_comment_theme_analysis.csv`
- **Columns:** `season`, `comment`, `keyword`, `star_negative/neutral/positive`, `star_top_label`, `star_top_score`, `tri_negative/neutral/positive`, `tri_top_label`, `tri_top_score`, `final_negative/neutral/positive`, `sentiment_association`, `decision_type`, `topic_category`, `llm_label`, `llm_reason`, `final_label_after_llm`

---

## Step 7: ADS Output

### 7a. Comment-Level Table

Extracts the five essential fields from the full analysis table.

**Function:** `build_ads_final_5_fields_dataframe()`

| Source Column | Final Column |
|---------------|--------------|
| `season` | `season` |
| `comment` | `comment` |
| `keyword` | `keyword` |
| `final_label_after_llm` | `sentiment_association` |
| `topic_category` | `topic_category` |

**Output:** `ads_comment_theme_analysis`
- **Path:** `data/ADS_Resource_Data/3_Processed/ads_comment_theme_analysis.csv`

### 7b. Season-Level Summary Table

Aggregates results into a per-season overview.

**Function:** `create_ads_season_overall_evaluation_dataframe()`

**Inputs:**
- `ads_comment_theme_analysis` — for sentiment counts per season
- `dws_season_rating_comparison` — for Douban and IMDB ratings

**Aggregation logic:**
1. Group by `season`, count occurrences of each `sentiment_association` value via `groupby("season")["sentiment_association"].value_counts().unstack(fill_value=0)`
2. Ensure all three sentiment columns exist (fill missing with 0)
3. Rename columns: `positive` → `positive_comment_cnt`, `negative` → `negative_comment_cnt`, `neutral` → `netral_common_cnt`
4. Compute `total_common_cnt = positive + negative + neutral`
5. Merge with rating data on `season_id` via left join
6. Fill any NaN counts with 0

**Final columns (8 fields):**
`season_id`, `df_douban_rating`, `imdb_rating`, `rating_difference`, `positive_comment_cnt`, `negative_comment_cnt`, `netral_common_cnt`, `total_common_cnt`

**Output:** `ads_season_overall_evaluation`
- **Path:** `data/ADS_Resource_Data/3_Processed/ads_season_overall_evaluation.csv`

---

## Technologies

| Technology | Purpose |
|------------|---------|
| **Transformers (Hugging Face)** | Pretrained NLP models for sentiment and spam detection |
| **KeyBERT** | Keyword extraction using semantic embeddings |
| **SnowNLP** | Chinese text processing and keyword extraction |
| **jieba** | Chinese word segmentation |
| **LLM APIs** | DeepSeek, Qwen, Kimi, MiniMax for sentiment review and topic classification |
| **PySpark** | Data processing and MongoDB integration |
| **MongoDB** | Data storage and retrieval |
| **Threading** | Concurrent model execution for throughput |

## Usage

1. Open `03_ADS_Code/ADS_Colab_260406_2207.ipynb` in **Google Colab with GPU** (Runtime → Change runtime type → GPU → T4)
2. Execute all cells in sequence
3. The notebook automatically installs required libraries
4. Results are saved to MongoDB and exported as CSV files

## Notes

- A **GPU** is required due to the computational demands of the AI models
- LLM API tokens must be configured in the `TOPIC_MODEL_CONFIGS` section
- Processing 2,000+ comments with multiple AI models and LLM calls requires significant time

---

[Return to English README](../README.md) / [返回中文 README](README_CN.md)

---
