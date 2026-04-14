# STAT_2630SEF_Group_Project

语言: [English](../README.md) / 中文

**课题：** 基于情感分析的中国观众对《老友记》接受度研究

**运行环境：** `Python 3.12+`

---

## 项目概述

本项目遵循数据仓库架构（ODS → DWS → ADS），构建完整的数据流水线，用于采集、处理、分析和可视化豆瓣平台上关于美剧《老友记》（Friends）的评论与评分数据。流水线覆盖从网页爬取、NLP 情感分析到交互式可视化的全流程。

## 项目结构

```
STAT_2630SEF_Group_Project/
├── 01_ODS_Scraper_Code/       # 数据爬取层（操作数据存储）
├── 02_DWS_Code/               # 数据仓库服务层
├── 03_ADS_Code/               # 应用数据服务层
├── 04_Visualization/          # Power BI 可视化仪表板
├── data/                      # 数据存储（ODS、DWS、ADS）
├── Docs/                      # 文档
└── README.md
```

## 模块文档

各模块的详细文档位于 `Docs/` 文件夹中：

| 模块 | 说明 | 文档链接 |
|------|------|----------|
| **01 ODS 爬虫** | 从豆瓣采集数据 | [English](./01_ODS_Scraper_Code.md) / [中文](./01_ODS_Scraper_Code_CN.md) |
| **02 DWS** | 数据清洗和聚合 | [English](./02_DWS_Code.md) / [中文](./02_DWS_Code_CN.md) |
| **03 ADS** | NLP 分析和情感分类 | [English](./03_ADS_Code.md) / [中文](./03_ADS_Code_CN.md) |
| **04 可视化** | Power BI 仪表板 | [English](./04_Visualization.md) / [中文](./04_Visualization_CN.md) |

## 数据流水线架构

### 1. ODS 层（数据采集）

位于 `01_ODS_Scraper_Code/`，使用 Scrapy 框架从豆瓣采集原始数据：

- **评分爬虫** (`rating/`)：从豆瓣搜索结果中提取《老友记》各季评分
- **评论爬虫** (`comment/`)：提取《老友记》第一季（条目 ID: 3286552）的用户评论，分页采集 20 页（约 400 条）
- **运行脚本** (`run_scraper.py`)：按顺序调度两个爬虫，输出至 `data/ODS_Resource_Data/`

**输出文件：** `rating.json`、`comment.json`

**详细文档：** [English](./01_ODS_Scraper_Code.md) / [中文](./01_ODS_Scraper_Code_CN.md)

### 2. DWS 层（数据处理）

位于 `02_DWS_Code/`，对原始数据进行清洗和聚合：

- 生成 `dws_season_rating_comparison` 表，对比各季豆瓣评分与 IMDB 评分
- 清洗并标准化原始评论数据，生成 `dws_douban_comment`
- 使用 DuckDB、Pandas 和 MongoDB 进行数据处理

**输出文件：** `dws_season_rating_comparison.csv`、`dws_douban_comment.csv`

**详细文档：** [English](./02_DWS_Code.md) / [中文](./02_DWS_Code_CN.md)

### 3. ADS 层（数据分析）

位于 `03_ADS_Code/`，执行核心分析工作：

- **数据过滤：** 两阶段过滤——先通过正则规则初筛，再使用多模型集成进行垃圾内容和毒性检测
- **文本预处理：** Jieba 中文分词与停用词过滤
- **情感分析：** 多模型委员会机制（5 星模型 + 3 值模型），对分歧案例引入 LLM 裁决
- **主题分类：** 基于 LLM API 将评论归类为演员、剧情、情怀三个主题
- **并发执行：** 多线程调度多个 LLM 端点，提升吞吐量并实现故障转移

**输出文件：**
- `ads_season_overall_evaluation.csv` — 各季综合评估表（含评分、情感分布）
- `ads_comment_theme_analysis.csv` — 评论主题分析表（含关键词、情感标签、主题分类）

**详细文档：** [English](./03_ADS_Code.md) / [中文](./03_ADS_Code_CN.md)

### 4. 可视化

位于 `04_Visualization/`，包含 Power BI 仪表板文件（`mgHurryo.pbix`），用于交互式探索分析结果。

**详细文档：** [English](./04_Visualization.md) / [中文](./04_Visualization_CN.md)

## 数据目录结构

```
data/
├── ODS_Resource_Data/         # 原始爬取数据（JSON 格式）
└── ADS_Resource_Data/
    ├── 1_Raw/                 # DWS 层输入数据
    ├── 2_Intermediate/        # 中间处理结果
    ├── 3_Processed/           # 最终 ADS 输出表
    └── 4_Backup/              # 数据备份
```

## 主要技术栈

- **网页爬虫：** Scrapy
- **数据处理：** DuckDB、Pandas、PyMongo、PySpark
- **自然语言处理：** Jieba、KeyBERT、SnowNLP、Hugging Face Transformers
- **LLM API：** DeepSeek、Qwen、Kimi、MiniMax
- **数据可视化：** Power BI
- **开发环境：** Google Colab（GPU/T4）、Jupyter Notebook

## 使用说明

1. **运行爬虫：**
   ```bash
   cd 01_ODS_Scraper_Code
   python run_scraper.py
   ```

2. **处理 DWS 层：**
   在 Jupyter/Colab 中打开 `02_DWS_Code/dws层生成.ipynb` 并运行所有单元格

3. **运行 ADS 分析：**
   在 Jupyter/Colab 中打开 `03_ADS_Code/ADS_Colab_260406_2207.ipynb` 并运行所有单元格

4. **查看可视化：**
   在 Power BI Desktop 中打开 `04_Visualization/mgHurryo.pbix`
