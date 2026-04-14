# 模块 02：DWS 代码

语言: [English](./02_DWS_Code.md) / 中文

## 概述

本模块是项目的数据处理层，负责将 ODS 层采集的原始数据进行清洗、结构化，并整合外部数据源（IMDB 评分），生成标准化的表格供后续分析使用。

## 目录结构

```
02_DWS_Code/
└── dws层生成.ipynb    # Jupyter Notebook（在 Google Colab 上运行）
```

整个 DWS 层由一个 Jupyter Notebook 实现，设计在 Google Colab 上运行。

## 处理任务

### 任务一：季评分对比表

**输入数据：**
- 豆瓣各季评分（来自 MongoDB `ods_data.ods_douban_season_rating`）
- IMDB 各集评分（来自 MongoDB `ods_data.ods_friends_episodes_v3`）

**处理流程：**
1. 连接 MongoDB，拉取两份评分数据
2. 从 IMDB 单集数据计算各季的平均评分
3. 按季将豆瓣评分与 IMDB 评分进行关联
4. 计算**评分差值**（豆瓣评分减去 IMDB 评分）

**输出表（`dws_season_rating_comparison`）：**

| season | df_douban_rating | imdb_rating | rating_difference |
|--------|-----------------|-------------|-------------------|
| 1      | 9.7             | 8.3         | 1.4               |
| 2      | 9.8             | 8.5         | 1.3               |
| 3      | 9.7             | 8.4         | 1.3               |
| ...    | ...             | ...         | ...               |

### 任务二：豆瓣评论表

**输入数据：**
- 原始豆瓣评论（来自 MongoDB `ods_data.ods_douban_comment`）

**处理流程：**
1. 从 MongoDB 拉取所有原始评论数据
2. 重命名并标准化列名：
   - `id` → `user_id`
   - `name` → `user_name`
   - `season` 和 `comment` 保持不变
3. 按季数排序

**输出表（`dws_douban_comment`）：**

| user_id | season | user_name | comment |
|---------|--------|-----------|---------|
| 199     | 1      | 猫猫eko   | 这个就不用我多说了吧。。。不笑除非你没长嘴。 |
| 350     | 1      | 日光瀑布  | 我的大学时光 |
| ...     | ...    | ...       | ...     |

## 使用的技术

| 技术 | 用途 |
|------|------|
| **DuckDB** | 本地数据上的快速 SQL 查询（轻量级分析数据库） |
| **Pandas** | 数据操作和表格处理 |
| **PyMongo** | 连接和读写 MongoDB |

## 数据流向

```
MongoDB（ODS 原始数据）
    ↓
DWS Notebook（DuckDB SQL + Pandas 处理）
    ↓
MongoDB（DWS 处理后数据）
    - dws_season_rating_comparison（季评分对比表）
    - dws_douban_comment（豆瓣评论表）
```

## 使用方法

1. 在 Google Colab 或 Jupyter Notebook 中打开 `02_DWS_Code/dws层生成.ipynb`
2. 安装依赖（Notebook 通过 `!pip install pymongo` 自动处理）
3. 按顺序执行所有单元格

---

[Return to English README](../README.md) / [返回中文 README](README_CN.md)

---