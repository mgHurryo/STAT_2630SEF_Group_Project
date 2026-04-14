# 模块 04：可视化

语言：[English](./04_Visualization.md) / 中文

## 概述

本模块将 ADS 层的分析结果以交互式图表和仪表板的形式呈现，便于直观地探索数据。

## 目录结构

```
04_Visualization/
└── mgHurryo.pbix    # Power BI Desktop 文件
```

仪表板使用 **Microsoft Power BI** 构建，以 `.pbix` 文件格式分发。

## 仪表板内容

Power BI 仪表板（`mgHurryo.pbix`）可视化了 ADS 层的输出，涵盖以下内容：

- **季评分对比：** 各季豆瓣评分与 IMDB 评分对比
- **情感分布：** 正面、负面、中立评论的比例
- **主题分布：** 评论在演员、剧情、情怀三个主题上的分布
- **关键词云：** 评论语料中出现频率最高的关键词
- **趋势分析：** 情感倾向和评分在各季之间的变化趋势

## 使用方法

1. 安装 **Power BI Desktop**（微软免费下载：https://powerbi.microsoft.com/desktop/）
2. 打开 `04_Visualization/mgHurryo.pbix`
3. 仪表板加载内置数据后即可浏览

## 数据来源

Power BI 文件嵌入了 ADS 输出表的数据：
- `ads_season_overall_evaluation.csv` — 季级汇总
- `ads_comment_theme_analysis.csv` — 评论级详细分析

底层数据更新后，可按以下步骤刷新数据源：
1. 点击 **主页 → 转换数据**
2. 更新文件路径，指向最新的 CSV 文件
3. 点击 **刷新** 重新加载数据

## 注意事项

- `.pbix` 文件为**二进制文件**，无法用文本编辑器查看或编辑
- 需要 Power BI Desktop 才能打开和修改仪表板
- 文件可发布至 Power BI Service（云端）进行在线分享
- 仅查看仪表板使用免费的 Power BI Desktop 即可

---

[Return to English README](../README.md) / [返回中文 README](README_CN.md)

---
