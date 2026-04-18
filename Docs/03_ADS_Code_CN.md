# 模块 03：ADS 代码

语言：[English](./03_ADS_Code.md) / 中文

## 概述

ADS（Application Data Service）是本项目的数据分析与结果生成核心模块，负责将 DWS 层整理后的评论数据转化为可解释、可汇报、可视化的应用层成果。模块围绕评论质量筛选、文本预处理、情感分析、主题分类与 ADS 标准结果构建展开，形成了一条完整的分析闭环。

本模块最终交付两类核心结果：

1. 评论级结果表 `ads_comment_theme_analysis`
2. 季级综合评价表 `ads_season_overall_evaluation`

## 目录结构

```text
03_ADS_Code/
└── ADS_Colab_260406_2207.ipynb
```

ADS 层以 Jupyter Notebook 形式实现，运行环境为 Google Colab 风格配置，并结合 Spark、MongoDB 与外部 LLM API 共同完成分析流程。

## 流水线概览

```text
DWS 评论数据
    ↓
步骤 1：规则预筛与去重     → dws_comment_rule_filtered
    ↓
步骤 2：多模型评论过滤     → dws_comment_model_filtered
    ↓
步骤 3：文本预处理         → dws_comment_preprocessed
    ↓
步骤 4：情感分析           → dws_comment_sentiment_analysis
    ↓
步骤 5：主题分类           → dws_comment_topic_analysis
    ↓
步骤 6：结果合并           → dws_comment_theme_analysis
    ↓
步骤 7：ADS 评论级输出     → ads_comment_theme_analysis
    ↓
步骤 8：ADS 季级汇总       → ads_season_overall_evaluation
```

## 技术架构

### 运行环境

| 项目 | 配置 |
|---|---|
| Python | `3.12+` |
| Spark | `4.0.2` |
| Scala | `2.13.16` |
| 数据库 | MongoDB |
| 执行环境 | Google Colab 风格环境 |

### 关键依赖

| 类别 | 依赖 |
|---|---|
| 基础工具 | `os`, `re`, `json`, `time`, `threading`, `queue` |
| 数据处理 | `pandas` |
| 中文文本处理 | `jieba`, `stopwords-zh`, `filter_stopwords`, `SnowNLP` |
| 关键词提取 | `KeyBERT`, `SentenceTransformer`, `CountVectorizer` |
| 模型推理 | `transformers`, `pipeline` |
| 并发执行 | `ThreadPoolExecutor`, `as_completed` |
| 数据库 | `pymongo`, `MongoClient` |
| 分布式处理 | `pyspark.sql.SparkSession` |
| API 调用 | `requests` |

### 数据流转路径

`MongoDB -> Spark -> Pandas -> Spark -> MongoDB + CSV`

这一结构既保证了批量读写能力，也支持评论文本分析阶段的灵活处理。

## 数据库与 CSV 工具层

Notebook 在主流程之前构建了一套通用工具层，用于统一数据库读写、CSV 导入导出和 Spark 会话管理，是整个 ADS 流程能够稳定复用的重要基础。

### 关键函数

| 函数 | 作用 |
|---|---|
| `connect_spark()` | 创建 SparkSession 并挂载 MongoDB Connector |
| `ensure_spark_session()` | 兼容 SparkSession 或 Mongo URI 输入 |
| `get_mongo_reader()` | 生成 MongoDB Reader |
| `get_mongo_writer()` | 生成 MongoDB Writer |
| `load_mongo_to_dataframe()` | 读取 MongoDB 集合并转为 DataFrame |
| `insert_dataframe_to_collection()` | 将结果写回 MongoDB |
| `export_dataframe_to_csv()` | 导出单一 CSV 文件 |
| `export_all_collections_to_csv()` | 批量导出所有集合 |

### 工具层价值

这一层实现让各阶段 pipeline 能共享相同的输入输出模式，从而保证整个 ADS 模块在结构上统一、在执行上顺畅、在交付上完整。

## 分阶段说明

## 步骤 1：规则预筛与去重

该阶段面向原始评论数据完成基础清洗与规则去重，主要包括：

- 删除空评论与空用户名
- 去除首尾空格与空字符串
- 过滤纯符号、纯数字与过短评论
- 对评论与用户名做标准化
- 按同季同用户、同季同内容、跨季相同内容三条规则进行去重

**输入：** `dws_douban_comment`  
**输出：** `dws_comment_rule_filtered`

运行结果：原始 `3999` 条评论经规则预筛后保留 `3552` 条，保留率为 `88.82%`。

---

## 步骤 2：多模型评论过滤

该阶段通过 4 个文本分类模型协同判断评论是否适合进入正式分析流程：

| 变量名 | 模型 | 功能 |
|---|---|---|
| `garbage` | `Titeiiko/OTIS-Official-Spam-Model` | 评论异常预筛 |
| `garbage2` | `textdetox/xlmr-large-toxicity-classifier-v2` | 攻击性评论识别 |
| `garbage3` | `mrm8488/bert-tiny-finetuned-sms-spam-detection` | 广告垃圾识别 |
| `garbage4` | `baptistejamin/xlm-roberta-large-spam_v4` | 常规 / 广告 / 乱码分类 |

综合评分公式如下：

```text
k2 = score2 if label2 == "LABEL_0" else 1 - score2
k3 = score3 if label3 == "LABEL_0" else 1 - score3
k4 = score4 if label4 == "regular" else 1 - score4

final_score = 0.2 * k2 + 0.35 * k3 + 0.45 * k4
```

评论在该阶段完成质量确认后写入 `dws_comment_model_filtered`。运行结果：`3552` 条评论中保留 `2499` 条，保留率为 `70.35`。

---

## 步骤 3：文本预处理

该阶段将评论转换为适合 NLP 分析的标准化文本，主要处理包括：

- 按句末标点分句
- 使用 `jieba` 完成中文分词
- 通过 `stopwords-zh` 去除停用词
- 清洗空 token 与纯符号 token
- 过滤过短句子
- 生成 `processed_comment`

**输入：** `dws_comment_model_filtered`  
**输出：** `dws_comment_preprocessed`

运行结果：`2499` 条评论经文本预处理后形成 `2285` 条标准化分析记录。

---

## 步骤 4：情感分析

情感分析采用多模型协同机制，对每条评论生成关键词、情感概率分布与最终情感标签。

### 使用模型

| 能力 | 模型 |
|---|---|
| 五星情感模型 | `nlptown/bert-base-multilingual-uncased-sentiment` |
| 三分类情感模型 | `cardiffnlp/twitter-xlm-roberta-base-sentiment` |
| 关键词提取 | `KeyBERT` + `paraphrase-multilingual-MiniLM-L12-v2` |
| 关键词辅助提取 | `SnowNLP` |
| LLM 复审 | `deepseek-chat` |

### 情感决策逻辑

- 五星模型先映射为三类情感分布
- 三分类模型直接输出正面 / 中立 / 负面分布
- 结合影视评论常见表达进行轻量偏置
- 双模型结果按 `0.6 / 0.4` 加权融合
- 对冲突评论交由 LLM 进行复审
- 对负面评论执行并发二次复审

**输入：** `dws_comment_preprocessed`  
**输出：** `dws_comment_sentiment_analysis`

输出结果表中包含：

- 评论关键词
- 五星模型分布与主标签
- 三分类模型分布与主标签
- 融合后的最终情感分布
- 情感标签与判定来源
- LLM 复审结果与最终标签

该阶段最终为全部 `2285` 条评论生成了可解释的情感分析结果。

---

## 步骤 5：主题分类

主题分类将评论统一归类为以下三个主题之一：

- `演员`
- `剧情`
- `情怀`

### 模型池设计

主题分类基于多模型池运行，候选模型包括 DeepSeek、Qwen、Kimi、MiniMax 等多个 API 配置。Notebook 在正式执行前先进行 Smoke Test 与并发压力测试，再将通过测试的模型纳入可用模型池。

**输入：** `dws_comment_preprocessed`  
**输出：** `dws_comment_topic_analysis`

运行结果：`2285` 条评论全部完成主题分类，并保留 `used_model` 字段用于追踪实际使用的模型。

---

## 步骤 6：情感与主题结果合并

该阶段将情感分析结果与主题分类结果合并为完整评论级分析表。

**输入：**

- `dws_comment_sentiment_analysis`
- `dws_comment_topic_analysis`

**输出：** `dws_comment_theme_analysis`

合并后的结果表同时保留：

- 评论基础信息
- 关键词
- 五星模型结果
- 三分类模型结果
- 融合后的情感结果
- 主题分类结果
- LLM 说明信息

运行结果：合并后共得到 `2285` 条完整评论分析记录。

---

## 步骤 7：生成 ADS 评论级结果表

该阶段将完整评论分析结果压缩为 ADS 标准五字段结构：

- `season`
- `comment`
- `keyword`
- `sentiment_association`
- `topic_category`

**输入：** `dws_comment_theme_analysis`  
**输出：** `ads_comment_theme_analysis`

运行结果：输出 `2285` 条 ADS 评论级结果。

---

## 步骤 8：生成 ADS 季级综合评价表

该阶段将评论级结果与季评分表进行聚合与融合，生成季级综合评价结果。

**输入：**

- `ads_comment_theme_analysis`
- `dws_season_rating_comparison`

**输出：** `ads_season_overall_evaluation`

结果表字段包括：

- `season_id`
- `df_douban_rating`
- `imdb_rating`
- `rating_difference`
- `positive_comment_cnt`
- `negative_comment_cnt`
- `netral_common_cnt`
- `total_common_cnt`

运行结果：共生成 `10` 条季级综合评价记录。

## 结果交付

Notebook 最终将原始表、中间表、分析表与结果表统一导出为 CSV，共计 10 张文件，包括：

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

