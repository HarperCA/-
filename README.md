# 量化分析报告页

当前项目只保留 `http://127.0.0.1:5001/analysis` 这一页，以及这页需要的分析、保存、分享、指标解释和报告追问接口。

## 启动

```powershell
.\run_web.ps1
```

浏览器访问：

```text
http://127.0.0.1:5001/analysis
```

## 保留内容

- 单标的量化分析表单
- 策略研究报告页面
- 报告图片访问
- 当前页的保存、分享、读者版本、指标解释和追问 API

## 目录结构

```text
.
├── agent/              # 分析编排与可选 LLM 解读
├── core/               # 数据获取、指标、回测和估值逻辑
├── reports/            # 图表生成器；运行时图片会生成在这里
├── web_modules/        # 当前分析页模板
├── data/               # 本地缓存、guest 状态和分享快照
├── logs/               # Web 服务日志
├── web_app.py          # 单页 Flask 应用
└── run_web.ps1         # 本地启动脚本
```

运行时生成的 `data/cache/`、`data/userspace/`、`data/shared_reports/`、`reports/*.png`、`logs/` 已放入 `.gitignore`，不作为项目源码维护。

## 说明

本页只用于投资复盘、风险识别和资料整理，不构成投资建议、买卖建议或收益承诺。
