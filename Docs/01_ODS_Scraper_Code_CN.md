# 模块 01：ODS 爬虫代码

语言: [English](./01_ODS_Scraper_Code.md) / 中文



## 概述

本模块是项目的数据采集层，使用 Scrapy 框架从豆瓣（中国影评平台）提取《老友记》的季评分和用户评论原始数据。

## 目录结构

```
01_ODS_Scraper_Code/
├── comment/               # 评论爬虫（Scrapy 项目）
│   ├── comment/
│   │   ├── spiders/
│   │   │   └── douban_comment.py   # 评论爬虫主体
│   │   ├── items.py                # 数据结构定义
│   │   ├── pipelines.py            # 数据处理管道
│   │   ├── middlewares.py          # 请求/响应中间件
│   │   └── settings.py             # 爬虫配置
│   └── scrapy.cfg                  # Scrapy 项目配置
├── rating/                # 评分爬虫（Scrapy 项目）
│   ├── rating/
│   │   ├── spiders/
│   │   │   └── rate.py             # 评分爬虫主体
│   │   ├── items.py                # 数据结构定义
│   │   ├── pipelines.py            # 数据处理管道
│   │   ├── middlewares.py          # 请求/响应中间件
│   │   └── settings.py             # 爬虫配置
│   └── scrapy.cfg                  # Scrapy 项目配置
└── run_scraper.py         # 统一运行脚本
```

## 爬虫说明

### 评分爬虫（`rating/`）

从豆瓣搜索结果中提取《老友记》各季的评分数据。

**工作流程：**
1. 在豆瓣搜索"老友记"
2. 解析前 10 个搜索结果，每个结果对应一季
3. 提取以下字段：
   - **季名**（如"老友记 第一季"）
   - **评分**（如 9.7）
   - **评分人数**（如 20 万）
4. 输出为 JSON 格式

**核心文件：** `rating/rating/spiders/rate.py`

### 评论爬虫（`comment/`）

从豆瓣提取《老友记》第一季的用户评论。

**工作流程：**
1. 访问《老友记》第一季的豆瓣页面（条目 ID: 3286552）
2. 每页解析 20 条评论，共采集 20 页（约 400 条）
3. 提取以下字段：
   - **评论 ID**（自动生成，从 3600 起始）
   - **季数**（固定为 10）
   - **评论内容**（原始文本）
   - **用户名**（作者）
4. 输出为 JSON 格式

**核心文件：** `comment/comment/spiders/douban_comment.py`

## 反检测措施

豆瓣设有机制限制自动化访问。爬虫采用以下策略应对：

- **User-Agent 伪装：** 标识为标准 Safari 浏览器
- **Cookie 认证：** 使用有效的豆瓣会话 Cookie，模拟已登录用户
- **请求间隔：** 设置 3 秒的请求延迟，避免对服务器造成过大压力
- **自动限速（Auto-throttle）：** 根据服务器响应时间动态调整请求频率
- **HTTP 缓存：** 缓存已访问页面，避免重复请求

## 运行脚本（`run_scraper.py`）

作为入口脚本，按顺序执行两个爬虫：

1. 运行**评分爬虫** → 输出至 `data/ODS_Resource_Data/rating.json`
2. 运行**评论爬虫** → 输出至 `data/ODS_Resource_Data/comment.json`
3. 报告各爬虫的执行状态

## 输出数据

| 文件 | 内容 | 格式 |
|------|------|------|
| `data/ODS_Resource_Data/rating.json` | 豆瓣各季评分数据 | JSON 数组 |
| `data/ODS_Resource_Data/comment.json` | 豆瓣用户评论数据 | JSON 数组 |

## 使用方法

```bash
cd 01_ODS_Scraper_Code
python run_scraper.py
```

## 注意事项

- 评论爬虫目前仅针对**第一季**（条目 ID: 3286552）。如需爬取其他季，需修改 URL
- 爬虫限制为 **20 页**（400 条评论）。如需增加页数，调整 `self.page <= 400` 条件

---

[Return to English README](../README.md) / [返回中文 README](README_CN.md)

---