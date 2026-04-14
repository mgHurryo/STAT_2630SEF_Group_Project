# 模块 03：ADS 代码

语言：[English](./03_ADS_Code.md) / 中文

## 概述

本模块是项目的分析核心。ADS 全称为 **Application Data Service（应用数据服务）**，从 DWS 层获取清洗后的数据，应用自然语言处理（NLP）和机器学习技术，从豆瓣评论中提取情感倾向、主题分类和关键词。

## 目录结构

```
03_ADS_Code/
└── ADS_Colab_XXXXXX_XXXX.ipynb 
```

ADS 层以 Jupyter Notebook 形式实现，设计在 **Google Colab GPU 环境**（T4）中运行，因为需要执行计算密集型的 AI 模型。

## 流水线概览

分析流水线包含七个阶段：

```
DWS 评论数据
    ↓
步骤 1：正则初筛         → dws_comment_rule_filtered
    ↓
步骤 2：模型精筛         → dws_comment_model_filtered
    ↓
步骤 3：文本预处理       → dws_comment_preprocessed
    ↓
步骤 4：情感分析         → dws_comment_sentiment_analysis
    ↓
步骤 5：主题分类         → dws_comment_topic_analysis
    ↓
步骤 6：合并结果         → dws_comment_theme_analysis
    ↓
步骤 7：ADS 输出         → ads_comment_theme_analysis + ads_season_overall_evaluation
```

---

## 步骤 1：正则初筛

基于规则的过滤器，在调用 AI 模型之前剔除低质量评论，降低计算成本。

**数据来源：** `dws_douban_comment`

### 实现细节

流水线按顺序链式调用以下函数：

1. **空值/空白处理：** `remove_null_comments()` 删除 NaN 行；`strip_comment_whitespace()` 去除首尾空格；`remove_blank_comments()` 删除空字符串
2. **文本标准化：** `normalize_comment_text()` 通过 `re.sub(r"\s+", "", text)` 去除所有内部空格；`normalize_username_text()` 将连续空格压缩为单个空格
3. **内容过滤：**
   - `is_all_symbol()` — 使用 `re.search(r"[\u4e00-\u9fffA-Za-z0-9]", text)` 检测纯符号评论
   - `is_all_number()` — 使用 `re.fullmatch(r"\d+", text)` 检测纯数字评论
   - `remove_short_comments()` — 过滤 `comment_clean` 长度 < 2 的评论
4. **去重（三条规则）：**
   - **规则一 — 同一用户、同一季：** `deduplicate_same_season_same_user()` 按 `(season, user_name_clean)` 分组，保留最长评论；长度相同时保留行序靠后的
   - **规则二 — 不同用户、同一季、相同内容：** `deduplicate_same_season_same_comment()` 对 `(season, comment_clean)` 去重
   - **规则三 — 跨季相同内容：** `remove_cross_season_same_comments()` 若同一 `comment_clean` 出现在超过一个不同的季中，删除所有出现记录

**输出：** `dws_comment_rule_filtered`
- **路径：** `data/ADS_Resource_Data/2_Intermediate/dws_comment_rule_filtered.csv`
- **字段：** `season`, `user_name`, `comment`

---

## 步骤 2：模型精筛

使用 **四个 AI 模型** 检测并删除垃圾内容、广告、乱码和恶意评论。

**数据来源：** `dws_comment_rule_filtered`

### 模型列表

| 变量 | 模型 ID | 检测目标 | 标签含义 |
|------|---------|---------|---------|
| `garbage` | `Titeiiko/OTIS-Official-Spam-Model` | 垃圾内容预筛 | LABEL_0=垃圾, LABEL_1=正常 |
| `garbage2` | `textdetox/xlmr-large-toxicity-classifier-v2` | 毒性/攻击性检测 | LABEL_0=正常, LABEL_1=攻击 |
| `garbage3` | `mrm8488/bert-tiny-finetuned-sms-spam-detection` | 广告/垃圾检测 | LABEL_0=正常, LABEL_1=广告 |
| `garbage4` | `baptistejamin/xlm-roberta-large-spam_v4` | 多分类垃圾检测 | spam, regular, gibberish |

### 打分公式

将每个模型的输出转换为"保留倾向分数"：

```
k2 = score2  if label2 == "LABEL_0"  else  1 - score2
k3 = score3  if label3 == "LABEL_0"  else  1 - score3
k4 = score4  if label4 == "regular"  else  1 - score4

final_score = 0.2 * k2 + 0.35 * k3 + 0.45 * k4
```

### 一票否决机制

若模型 1 将评论标记为垃圾（LABEL_0），无论其他模型打分如何，最终分数强制设为 0。

### 判定

`final_score >= 0.6` 的评论予以保留，其余剔除。模型以 32 条为一批次调用，提升效率。

**输出：** `dws_comment_model_filtered`
- **路径：** `data/ADS_Resource_Data/2_Intermediate/dws_comment_model_filtered.csv`
- **字段：** `season`, `user_name`, `comment`（打分列在过滤后删除）

---

## 步骤 3：文本预处理

通过分句、分词和噪声去除，为 NLP 分析准备评论文本。

**数据来源：** `dws_comment_model_filtered`

### 实现细节

1. **分句：** `split_sentences()` 使用 `re.split(r'[。！？!?；;…]+|\.(?=\s|$)', text)` 按句末标点切分。逗号保留在句子内部。
2. **分词：** 每个句子使用 `jieba.cut()` 分词，然后通过 `stopwords-zh` 库的 `filter_stopwords()` 去除停用词。
3. **词元清洗：** `clean_tokens()` 去除空白词元和匹配 `re.fullmatch(r'[\W_]+', token)` 的纯非词字符词元。
4. **短句过滤：** 清洗后有效词元少于 2 个的句子被丢弃。
5. **文本重组：** 有效的处理后句子以 `"."` 为分隔符拼接。

**输出：** `dws_comment_preprocessed`
- **路径：** `data/ADS_Resource_Data/2_Intermediate/dws_comment_preprocessed.csv`
- **字段：** `season`, `comment`, `processed_comment`

---

## 步骤 4：情感分析

使用多模型集成方法，将每条评论分类为正面、负面或中立，并引入 LLM 仲裁机制。

**数据来源：** `dws_comment_preprocessed`

### 模型组成

| 组件 | 模型 ID | 功能 |
|------|---------|------|
| 5 星模型 | `nlptown/bert-base-multilingual-uncased-sentiment` | 对文本进行 1–5 星评分 |
| 3 值模型 | `cardiffnlp/twitter-xlm-roberta-base-sentiment` | 分类为正面/中立/负面 |
| 关键词提取器 | KeyBERT + `paraphrase-multilingual-MiniLM-L12-v2` | 语义关键词提取 |
| LLM 复审器 | DeepSeek / Qwen / Kimi（通过 API） | 处理歧义案例和负面复审 |

### 分数转换

**5 星 → 情感分布：**
- 1 星 → `negative += score`
- 2 星 → `negative += score * 0.7`, `neutral += score * 0.3`
- 3 星 → `neutral += score`
- 4 星 → `positive += score * 0.7`, `neutral += score * 0.3`
- 5 星 → `positive += score`

分数随后归一化，使总和为 1.0。

**3 值 → 分布：** 直接映射（label_0 → negative, label_1 → neutral, label_2 → positive），然后归一化。

### 领域词组偏置

预定义的正则表达式模式列表（`positive_patterns`, `negative_patterns`）与原始评论进行匹配。若匹配到正面模式（且无负面模式），则在两个分布中给正面分数 `+0.08`；负面模式同理。偏置应用后重新归一化。

### 决策逻辑（4 个分支）

| 条件 | 处理方式 |
|------|---------|
| 双模型均不确定（`star_top_score <= 0.35` 且 `tri_top_score <= 0.35`） | 强制结果为 `neutral`（1.0） |
| 模型强烈分歧（一个预测正面，另一个预测负面） | 调用 LLM，使用 LLM 标签作为 1.0 one-hot |
| 标签不同且置信度差距较大（`abs(star_top_score - tri_top_score) >= 0.25`） | 调用 LLM，使用 LLM 标签作为 1.0 one-hot |
| 正常情况 | 加权融合：`final = 0.6 * star_dist + 0.4 * tri_dist`，取 argmax |

### 方向保护

加权融合后执行安全检查：
- 若两模型均未检测到"负面"但融合结果为"负面" → 移除"负面"，在 {中立, 正面} 上重新归一化
- 若两模型均未检测到"正面"但融合结果为"正面" → 同理处理

### LLM 负面复审

所有标记为"负面"的评论通过 `ThreadPoolExecutor`（多线程）进行额外的 LLM 复审。若 LLM 将评论重新分类为中立或正面，则更新标签；否则保持负面。

### 关键词提取（`extract_one_keyword`）

1. 尝试 KeyBERT 提取，参数 `keyphrase_ngram_range=(1, 2)`, `top_n=3` — 取第一个有效关键词
2. 使用 jieba 分词，过滤出 2–8 个字符的词元（无空格、无纯符号、无纯数字）
3. 尝试 SnowNLP 关键词提取
4. 降级方案：返回第一个清洗后的词元，或空字符串

### 句子级处理

评论被拆分为句子（每段最长 120 字符）。每个句子独立分析，结果按句子长度比例（`sent_len / total_len`）加权平均。

**输出：** `dws_comment_sentiment_analysis`
- **路径：** `data/ADS_Resource_Data/2_Intermediate/dws_comment_sentiment_analysis.csv`
- **关键字段：** `season`, `comment`, `keyword`, `star_negative/neutral/positive`, `tri_negative/neutral/positive`, `final_negative/neutral/positive`, `sentiment_association`, `decision_type`, `llm_label`, `llm_reason`, `final_label_after_llm`

---

## 步骤 5：主题分类

将每条评论归入以下三个主题之一：**演员**、**剧情**、**情怀**。

**数据来源：** `dws_comment_preprocessed`

### LLM 模型池

配置了多个 LLM API，每个模型有独立设置：

| 模型 | 端点 | 线程数 |
|------|------|--------|
| `deepseek-chat` | api.deepseek.com | 20 |
| `deepseek-v3.2-exp` | dashscope.aliyuncs.com | 10 |
| `kimi-k2.5` | dashscope.aliyuncs.com | 8 |
| `MiniMax-M2.5` | dashscope.aliyuncs.com | 8 |
| `deepseek-v3.1` | dashscope.aliyuncs.com | 8 |
| `qwen-turbo-latest` | dashscope.aliyuncs.com | 8 |
| `qwen-turbo` | dashscope.aliyuncs.com | 8 |

每个模型配置 `timeout=60s`，`max_retries=3`。

### 模型评估

正式使用前，模型需经过两阶段评估：

1. **连通性测试（Smoke Test）：** 用固定测试评论进行单次调用，验证连接和响应有效性。失败的模型直接淘汰。
2. **压力测试：** 通过连通性测试的模型接收并发请求（`thread_workers * 2` 轮），使用 5 条轮换测试评论。仅成功率 ≥ 80% 的模型进入生产池（`AVAILABLE_TOPIC_MODELS`）。

### 并发处理架构

每个可用模型封装在一个 `TopicModelWorker` 中，拥有独立的 `ThreadPoolExecutor`：

- **任务分发：** 评论通过轮询方式（`idx % len(model_workers)`）分配给各 worker，使用线程安全的 `queue.Queue()`
- **Worker 执行：** 每个 worker 线程运行 `worker_loop()`，持续从队列中拉取任务
- **故障转移：** 若某模型在特定评论上失败，自动切换至池中下一个可用模型。若所有模型均失败，该评论标记为"其他"
- **重试机制：** 每次 API 调用使用指数退避：`time.sleep(1.5 * (attempt + 1))`
- **结果同步：** 结果存储在受 `threading.Lock()` 保护的共享 `result_dict` 中。`task_queue.join()` 确保所有任务完成后才进行结果汇总

### LLM 提示词

提示词指示模型将评论归入候选标签之一，并以 JSON 格式返回 `{"topic_category": "label", "reason": "explanation"}`。若 JSON 解析失败，使用正则表达式回退解析。

**输出：** `dws_comment_topic_analysis`
- **路径：** `data/ADS_Resource_Data/2_Intermediate/dws_comment_topic_analysis.csv`
- **字段：** `season`, `comment`, `topic_category`, `llm_topic_reason`, `used_model`

---

## 步骤 6：合并情感与主题结果

将情感分析结果和主题分类结果合并为一张综合表。

**数据来源：** `dws_comment_sentiment_analysis` + `dws_comment_topic_analysis`

### 实现

1. 主题表按 `(season, comment)` 去重，保留最后一条
2. 执行左连接：`sentiment_df.merge(topic_df[[season, comment, topic_category]], on=[season, comment], how="left")`
3. 未匹配的主题值填充为"其他"
4. 合并后的表保留所有情感分数、最终标签、决策类型和主题分类（共 25 个字段）

**输出：** `dws_comment_theme_analysis`
- **路径：** `data/ADS_Resource_Data/2_Intermediate/dws_comment_theme_analysis.csv`
- **字段：** `season`, `comment`, `keyword`, `star_negative/neutral/positive`, `star_top_label`, `star_top_score`, `tri_negative/neutral/positive`, `tri_top_label`, `tri_top_score`, `final_negative/neutral/positive`, `sentiment_association`, `decision_type`, `topic_category`, `llm_label`, `llm_reason`, `final_label_after_llm`

---

## 步骤 7：ADS 输出

### 7a. 评论级表

从完整分析表中提取五个核心字段。

**函数：** `build_ads_final_5_fields_dataframe()`

| 源字段 | 最终字段 |
|--------|---------|
| `season` | `season` |
| `comment` | `comment` |
| `keyword` | `keyword` |
| `final_label_after_llm` | `sentiment_association` |
| `topic_category` | `topic_category` |

**输出：** `ads_comment_theme_analysis`
- **路径：** `data/ADS_Resource_Data/3_Processed/ads_comment_theme_analysis.csv`

### 7b. 季级汇总表

将结果聚合为各季概览。

**函数：** `create_ads_season_overall_evaluation_dataframe()`

**输入：**
- `ads_comment_theme_analysis` — 用于各季情感计数
- `dws_season_rating_comparison` — 用于豆瓣和 IMDB 评分

**聚合逻辑：**
1. 按 `season` 分组，统计每个 `sentiment_association` 值的出现次数：`groupby("season")["sentiment_association"].value_counts().unstack(fill_value=0)`
2. 确保三个情感列都存在（缺失则填 0）
3. 重命名列：`positive` → `positive_comment_cnt`, `negative` → `negative_comment_cnt`, `neutral` → `netral_common_cnt`
4. 计算 `total_common_cnt = positive + negative + neutral`
5. 通过左连接将评分数据按 `season_id` 合并
6. 将 NaN 计数填充为 0

**最终字段（8 个）：**
`season_id`, `df_douban_rating`, `imdb_rating`, `rating_difference`, `positive_comment_cnt`, `negative_comment_cnt`, `netral_common_cnt`, `total_common_cnt`

**输出：** `ads_season_overall_evaluation`
- **路径：** `data/ADS_Resource_Data/3_Processed/ads_season_overall_evaluation.csv`

---

## 使用的技术

| 技术 | 用途 |
|------|------|
| **Transformers（Hugging Face）** | 预训练 NLP 模型，用于情感和垃圾评论检测 |
| **KeyBERT** | 基于语义嵌入的关键词提取 |
| **SnowNLP** | 中文文本处理和关键词提取 |
| **jieba** | 中文分词 |
| **LLM API** | DeepSeek、Qwen、Kimi、MiniMax，用于情感复审和主题分类 |
| **PySpark** | 数据处理和 MongoDB 集成 |
| **MongoDB** | 数据存储和读取 |
| **Threading** | 并发模型执行，提升吞吐量 |

## 使用方法

1. 在 **Google Colab GPU 环境**中打开 `03_ADS_Code/ADS_Colab_260406_2207.ipynb`（运行时 → 更改运行时类型 → GPU → T4）
2. 按顺序执行所有单元格
3. Notebook 会自动安装所需库
4. 结果保存至 MongoDB 并导出为 CSV 文件

## 注意事项

- 需要 **GPU**，AI 模型的计算需求较高
- LLM API 密钥需在 `TOPIC_MODEL_CONFIGS` 部分配置
- 使用多个 AI 模型和 LLM 调用处理 2,000+ 条评论需要较长时间

---

[Return to English README](../README.md) / [返回中文 README](README_CN.md)

---
