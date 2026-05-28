# -*- coding: utf-8 -*-
from __future__ import annotations

PAGE_TEMPLATE = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>量化分析报告工作台</title>
  <style>
    :root { --bg:#fff; --panel:#fff; --panel-2:#f8fafc; --ink:#111827; --muted:#6b7280; --line:#dfe5ec; --line-2:#edf1f5; --brand:#2563eb; --brand-dark:#1d4ed8; --ok:#087443; --warn:#b54708; --danger:#b42318; --shadow:none; }
    * { box-sizing:border-box; }
    body { margin:0; min-height:100vh; color:var(--ink); background:var(--bg); font:14px/1.45 "Microsoft YaHei","PingFang SC",Arial,sans-serif; }
    a { color:inherit; text-decoration:none; }
    h1,h2,h3,p { margin:0; }
    h1 { font-size:26px; line-height:1.2; letter-spacing:0; }
    h2 { font-size:16px; line-height:1.35; }
    h3 { font-size:14px; line-height:1.35; }
    .muted { color:var(--muted); }
    .mono { font-family:Consolas,"SFMono-Regular","Microsoft YaHei",monospace; }
    .top-nav { height:52px; padding:0 20px; display:grid; grid-template-columns:1fr auto 1fr; align-items:center; border-bottom:1px solid var(--line); background:#fff; }
    .brand-lockup { display:flex; align-items:center; gap:18px; font-weight:900; }
    .menu-mark { font-size:22px; line-height:1; font-weight:500; }
    .brand-mark { width:30px; height:30px; border:0; border-radius:0; display:grid; place-items:center; color:#111827; background:#fff; font:900 24px Consolas,monospace; }
    .report-title { text-align:center; }
    .report-title small { margin-left:10px; color:var(--muted); font:12px Consolas,monospace; }
    .nav-actions { justify-self:end; display:flex; align-items:center; gap:10px; color:#344054; font-size:13px; }
    .nav-actions form { margin:0; }
    .auth-btn,.chip,button { min-height:32px; display:inline-flex; align-items:center; justify-content:center; gap:6px; border:1px solid var(--line); border-radius:5px; background:#fff; color:#344054; padding:6px 10px; font-weight:700; cursor:pointer; }
    button.primary,.primary { border-color:var(--brand); background:var(--brand); color:#fff; }
    .secondary { border-color:var(--brand); background:var(--brand); color:#fff; }
    .ghost { background:#fff; color:#344054; }
    .tiny-button { min-height:28px; padding:4px 8px; font-size:12px; }
    .user-name { padding:5px 9px; border:1px solid var(--line); border-radius:5px; background:#f8fafc; font-weight:700; }
    .market-strip { display:none; }
    .shell { max-width:none; padding:0; }
    .hero { display:none; }
    .layout { height:calc(100vh - 52px); min-height:680px; display:grid; grid-template-columns:255px minmax(740px,1fr) 300px; overflow:hidden; }
    .side-rail { display:none; }
    .stack { display:contents; }
    .panel { background:var(--panel); border:0; border-radius:0; box-shadow:none; }
    .panel-head,.result-head { display:flex; justify-content:space-between; gap:12px; align-items:flex-start; margin-bottom:12px; padding-bottom:0; border-bottom:0; }
    .panel-tag,.eyebrow { display:none; }
    .field { display:grid; gap:6px; margin-bottom:12px; }
    label { font-size:12px; font-weight:800; color:#344054; }
    input,select,textarea { width:100%; border:1px solid #d8dee6; border-radius:5px; padding:8px 9px; color:var(--ink); background:#fff; font:inherit; }
    textarea { min-height:94px; resize:vertical; }
    input:focus,select:focus,textarea:focus { outline:2px solid rgba(37,99,235,.12); border-color:var(--brand); }
    .row-2 { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
    .actions,.chip-row,.holding-actions { display:flex; flex-wrap:wrap; align-items:center; gap:8px; }
    .left-rail { grid-column:1; padding:14px 18px 120px; border-right:1px solid var(--line); background:#fff; overflow:auto; }
    .report-main { grid-column:2; padding:14px 16px 120px; background:#fff; overflow:auto; border-right:1px solid var(--line); }
    .right-rail { grid-column:3; padding:14px 16px 120px; background:#fff; overflow:auto; }
    #agent-panel,#direct-panel { padding:0; }
    #agent-panel { margin-top:18px; display:none; }
    #history,#holdings-panel,#alerts-panel,#automation-panel,.module-launcher { display:none; }
    .result-panel { padding:0; background:#fff; color:var(--ink); }
    .result-panel .muted { color:var(--muted); }
    .result-panel .chip { color:#344054; background:#fff; border-color:var(--line); }
    .section-title { display:flex; align-items:center; gap:8px; margin:12px 0 8px; font-weight:900; }
    .section-title::before { content:""; width:3px; height:18px; background:var(--brand); border-radius:2px; }
    .summary-box { padding:0; border:0; border-radius:0; background:#fff; }
    .summary-box strong { display:block; margin-bottom:5px; font-size:15px; }
    .kpis { display:grid; grid-template-columns:repeat(6,minmax(90px,1fr)); border:1px solid var(--line); border-radius:5px; overflow:hidden; margin-bottom:12px; }
    .kpi { min-width:0; padding:12px 10px; text-align:center; background:#fff; border-right:1px solid var(--line); }
    .kpi:last-child { border-right:0; }
    .kpi span { display:block; color:var(--muted); font-size:12px; margin-bottom:4px; }
    .kpi strong { display:block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font:900 18px/1.2 Consolas,"Microsoft YaHei",monospace; }
    .report-box { white-space:pre-wrap; max-height:440px; overflow:auto; padding:14px; border:1px solid var(--line); border-radius:6px; background:#fff; color:#1f2937; font:13px/1.72 Consolas,"Microsoft YaHei",monospace; }
    .report-grid-2 { display:grid; grid-template-columns:1.05fr .95fr; gap:14px; align-items:start; }
    .mini-chart { min-height:190px; border:1px solid var(--line); border-radius:5px; background:#fff; overflow:hidden; }
    .mini-chart svg { width:100%; height:190px; display:block; }
    .metric-table { border:1px solid var(--line); border-radius:6px; overflow:auto; background:#fff; }
    .metric-table table { min-width:680px; }
    .metric-table td,.metric-table th { text-align:center; padding:7px 8px; }
    .metric-table td:first-child,.metric-table th:first-child { text-align:left; }
    .explain-button { min-height:24px; padding:2px 7px; border:1px solid #bfdbfe; border-radius:5px; background:#eff6ff; color:#1d4ed8; font:800 12px/1.4 "Microsoft YaHei","PingFang SC",Arial,sans-serif; }
    .explain-button:hover { background:#dbeafe; }
    .explain-modal { position:fixed; inset:0; z-index:40; display:none; place-items:center; padding:20px; background:rgba(15,23,42,.28); }
    .explain-modal.active { display:grid; }
    .explain-dialog { width:min(460px,calc(100vw - 32px)); border:1px solid var(--line); border-radius:8px; background:#fff; box-shadow:0 20px 50px rgba(15,23,42,.18); }
    .explain-head { display:flex; align-items:center; justify-content:space-between; gap:12px; padding:14px 16px; border-bottom:1px solid var(--line); }
    .explain-head strong { font-size:16px; }
    .explain-close { width:30px; min-height:30px; padding:0; border-radius:5px; }
    .explain-body { padding:15px 16px 18px; color:#344054; line-height:1.7; }
    .pos { color:var(--ok); font-weight:800; }
    .neg { color:var(--danger); font-weight:800; }
    .heat { text-align:center; font-family:Consolas,"Microsoft YaHei",monospace; }
    .heat.pos { background:#e9f7ef; }
    .heat.neg { background:#fff0ed; }
    .bar-cell { min-width:116px; }
    .bar { height:7px; border-radius:999px; background:#e8eef5; overflow:hidden; }
    .bar i { display:block; height:100%; background:#8fb6ff; }
    .agent-card { display:grid; grid-template-columns:1fr auto; gap:12px; padding:13px 14px; border:1px solid #bfdbfe; border-radius:6px; background:#eff6ff; }
    .agent-card strong { display:block; margin-bottom:4px; }
    .followup-box { grid-column:1 / -1; display:none; gap:8px; margin-top:8px; }
    .followup-box.active { display:grid; }
    .followup-output { display:grid; gap:8px; max-height:220px; overflow:auto; }
    .followup-message { padding:10px 12px; border:1px solid var(--line); border-radius:6px; background:#fff; color:#344054; line-height:1.6; white-space:pre-wrap; }
    .followup-message.user { background:#f8fafc; font-weight:800; }
    .reader-switch { display:grid; grid-template-columns:1fr 1fr; gap:6px; }
    .reader-switch .chip { justify-content:center; }
    .reader-switch .active,.tabs .active { color:#fff; background:var(--brand); border-color:var(--brand); }
    .reader-note,.action-feedback { margin-top:10px; padding:10px 12px; border:1px solid var(--line); border-radius:6px; background:#f8fafc; color:#344054; line-height:1.6; }
    .image-grid { display:grid; gap:14px; margin-top:14px; }
    .image-card { border:1px solid var(--line); border-radius:6px; overflow:hidden; background:#fff; }
    .image-card img { width:100%; min-height:320px; object-fit:contain; display:block; background:#f8fafc; }
    .image-card div { padding:9px 12px; color:#475467; font-size:12px; font-weight:800; border-top:1px solid var(--line); }
    .equity-chart { width:100%; height:360px; display:block; background:#fff; }
    .assumption-list,.export-list,.check-list { display:grid; gap:0; border:0; border-radius:0; overflow:hidden; background:#fff; }
    .assumption-list div,.check-list div { display:grid; grid-template-columns:1fr auto; gap:10px; padding:9px 0; border-bottom:1px solid var(--line-2); font-size:13px; }
    .assumption-list div:last-child,.check-list div:last-child { border-bottom:0; }
    .assumption-list b,.check-list b { font-weight:800; color:#344054; }
    .export-list a,.export-list button { width:100%; min-height:34px; border:1px solid var(--line); border-radius:5px; justify-content:center; margin-bottom:8px; }
    .export-list .primary { border-color:var(--brand); }
    .export-list a:last-child,.export-list button:last-child { border-bottom:0; }
    .risk-badge { display:inline-flex; justify-content:center; min-width:84px; padding:5px 10px; border-radius:5px; background:#fff4d6; color:var(--warn); font-weight:900; }
    .notice { padding:10px 12px; border:1px solid #fed7aa; border-radius:6px; background:#fff7ed; color:#9a3412; margin-bottom:12px; }
    .error { background:#fef2f2; color:var(--danger); border-color:#fecaca; }
    table { width:100%; border-collapse:collapse; font-size:13px; }
    th,td { text-align:left; padding:9px 8px; border-bottom:1px solid var(--line); }
    th { background:#f8fafc; color:#475467; font-size:12px; font-weight:900; }
    .subtle-card { border:1px solid var(--line); border-radius:6px; overflow:auto; background:#fff; }
    .record-grid { display:grid; gap:8px; }
    .record { display:flex; justify-content:space-between; gap:12px; padding:10px; border:1px solid var(--line); border-radius:6px; background:#fff; }
    .record-title { font-weight:900; }
    .record-meta,.record-tag { color:var(--muted); font-size:12px; }
    .history-scroll { max-height:520px; overflow:auto; }
    .data-card { margin-top:32px; padding:14px 8px; border:1px solid var(--line-2); border-radius:6px; background:#fff; }
    .data-card strong { display:block; margin-bottom:10px; }
    .data-row { display:flex; justify-content:space-between; padding:5px 0; color:var(--muted); font-size:12px; }
    .dot-ok { display:inline-block; width:7px; height:7px; border-radius:999px; background:#61b980; margin-left:6px; }
    .toggle-row { display:grid; gap:10px; margin:12px 0; }
    .toggle-row label { display:flex; justify-content:space-between; align-items:center; gap:8px; font-weight:500; color:#374151; }
    .switch { width:30px; height:18px; border-radius:999px; background:#cbd5e1; position:relative; flex:0 0 auto; }
    .switch::after { content:""; position:absolute; top:2px; left:2px; width:14px; height:14px; border-radius:999px; background:#fff; box-shadow:0 1px 2px rgba(0,0,0,.2); }
    .switch.on { background:var(--brand); }
    .switch.on::after { left:14px; }
    .switch { cursor:pointer; }
    .toggle-row label { cursor:pointer; }
    .range-buttons { display:grid; grid-template-columns:repeat(4,1fr); gap:7px; margin-top:8px; }
    .range-buttons button { min-height:30px; padding:4px 6px; }
    .left-rail input,.left-rail select,.left-rail button { min-width:0; }
    .left-rail .row-2 { grid-template-columns:1fr; }
    .left-rail .range-buttons { grid-template-columns:repeat(2,minmax(0,1fr)); }
    .left-rail .range-buttons button { width:100%; white-space:nowrap; }
    .workflow { position:fixed; left:0; right:0; bottom:0; z-index:5; display:grid; grid-template-columns:255px repeat(8,1fr) 300px; gap:0; padding:12px 16px 10px; border-top:1px solid var(--line); background:rgba(255,255,255,.98); box-shadow:0 -4px 14px rgba(16,24,40,.04); }
    .workflow-title { align-self:start; font-weight:900; }
    .workflow-title::before { content:""; display:inline-block; width:3px; height:18px; background:var(--brand); border-radius:2px; margin-right:8px; vertical-align:-4px; }
    .step { min-width:0; display:grid; gap:4px; justify-items:center; text-align:center; color:#667085; font-size:12px; }
    .step b { width:22px; height:22px; border-radius:999px; display:grid; place-items:center; background:var(--brand); color:#fff; font:800 12px Consolas,monospace; }
    .step span { max-width:100%; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    .workflow-status { display:grid; align-content:center; justify-items:end; color:#475467; font-size:12px; }
    .submit-overlay { position:fixed; inset:0; display:none; place-items:center; background:rgba(16,24,40,.18); z-index:20; }
    .submit-overlay.active { display:grid; }
    .submit-card { width:min(360px,calc(100vw - 32px)); padding:22px; border-radius:8px; background:#fff; text-align:center; border:1px solid var(--line); box-shadow:var(--shadow); }
    .spinner { width:34px; height:34px; margin:0 auto 14px; border-radius:999px; border:4px solid rgba(37,99,235,.14); border-top-color:var(--brand); animation:spin .8s linear infinite; }
    @keyframes spin { to { transform:rotate(360deg); } }
    body:not(.module-analysis) .layout { display:block; min-height:calc(100vh - 56px); padding:18px; }
    body:not(.module-analysis) .left-rail,body:not(.module-analysis) .report-main,body:not(.module-analysis) .right-rail,body:not(.module-analysis) .workflow { display:none; }
    .portfolio-head { display:grid; grid-template-columns:minmax(0,1fr) auto; gap:14px; align-items:start; margin-bottom:16px; }
    .portfolio-head h2 { font-size:22px; }
    .portfolio-actions { display:flex; flex-wrap:wrap; gap:8px; justify-content:flex-end; }
    .portfolio-kpis { display:grid; grid-template-columns:repeat(4,minmax(140px,1fr)); border:1px solid var(--line); border-radius:6px; overflow:hidden; margin-bottom:14px; background:#fff; }
    .portfolio-kpi { min-width:0; padding:14px 12px; border-right:1px solid var(--line); }
    .portfolio-kpi:last-child { border-right:0; }
    .portfolio-kpi span { display:block; color:var(--muted); font-size:12px; margin-bottom:6px; font-weight:800; }
    .portfolio-kpi strong { display:block; font:900 22px/1.2 Consolas,"Microsoft YaHei",monospace; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .portfolio-grid { display:grid; grid-template-columns:360px minmax(0,1fr); gap:14px; align-items:start; }
    .portfolio-card { border:1px solid var(--line); border-radius:6px; background:#fff; padding:14px; }
    .portfolio-card h3 { margin:0 0 10px; font-size:15px; }
    .diagnosis-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; margin-bottom:14px; }
    .diagnosis-card { min-height:104px; padding:13px; border:1px solid var(--line); border-radius:6px; background:#fff; display:grid; gap:8px; }
    .diagnosis-card b { font-size:15px; }
    .diagnosis-card span { color:var(--muted); font-size:12px; line-height:1.55; }
    .diagnosis-score { display:inline-flex; width:max-content; padding:4px 8px; border-radius:5px; background:#e6f4f1; color:#0f766e; font-weight:900; font-size:12px; }
    .diagnosis-score.warn { background:#fff4d6; color:var(--warn); }
    .diagnosis-score.danger { background:#fee2e2; color:var(--danger); }
    .portfolio-table-wrap { border:1px solid var(--line); border-radius:6px; overflow:auto; background:#fff; }
    .empty-portfolio { display:grid; gap:8px; padding:28px; text-align:center; color:var(--muted); }
    body.module-holdings #holdings-panel,body.module-alerts #alerts-panel,body.module-automation #automation-panel,body.module-history #history { display:block; max-width:1280px; margin:0 auto; padding:18px; border:1px solid var(--line); border-radius:6px; }
    @media (max-width:1180px) { .layout { grid-template-columns:260px minmax(0,1fr); } .right-rail { grid-column:1 / -1; border-top:1px solid var(--line); } .report-main { border-right:0; } .report-grid-2 { grid-template-columns:1fr; } .workflow { grid-template-columns:repeat(4,1fr); position:static; } .workflow-status { justify-items:start; } }
    @media (max-width:760px) { .top-nav { height:auto; min-height:56px; grid-template-columns:1fr; gap:8px; padding:10px 14px; } .report-title { text-align:left; } .nav-actions { justify-self:start; } .layout { display:block; } .left-rail,.report-main,.right-rail { border:0; padding:14px; } .kpis,.row-2,.portfolio-grid,.portfolio-kpis,.diagnosis-grid { grid-template-columns:1fr; } .kpi,.portfolio-kpi { border-right:0; border-bottom:1px solid var(--line); } .workflow { grid-template-columns:1fr 1fr; } table { min-width:640px; } .portfolio-head { grid-template-columns:1fr; } .portfolio-actions { justify-content:flex-start; } }
  </style>
</head>
<body class="{% if module_view %}module-view module-{{ module_view }}{% else %}module-dashboard module-analysis{% endif %}">
  <div class="submit-overlay" id="submitOverlay"><div class="submit-card"><div class="spinner"></div><strong>正在分析</strong><div class="muted">数据源偶尔会慢一点，完成后会自动显示结果。</div></div></div>
  <div style="display:none;">自然语言 Agent 结构化分析 开始分析 持仓管理</div>
  <nav class="top-nav">
    <div class="brand-lockup"><span class="menu-mark">☰</span><span class="brand-mark">♜</span></div>
    <div class="report-title"><h1>{% if module_view == 'holdings' %}组合诊断报告{% elif module_view == 'alerts' %}风险预警工作台{% elif module_view == 'automation' %}自动化任务中心{% elif module_view == 'history' %}历史复盘库{% elif result and result.market == 'fund' %}基金量化分析报告{% elif result and result.market == 'a_stock' %}股票量化分析报告{% elif result and result.market == 'crypto' %}数字资产量化分析报告{% elif result %}标的量化分析报告{% else %}策略研究报告{% endif %}<small>v2.0.5</small></h1></div>
    <div class="nav-actions"><span>报告生成时间：{{ result.generated_at if result and result.generated_at else "2025-05-24 15:30:21" }}</span><button type="button" class="auth-btn ghost js-save-report">保存</button>{% if result and result.standard_report_id %}<a class="auth-btn ghost" href="{{ url_for('download_research_report', report_id=result.standard_report_id, fmt='pdf') }}">导出 PDF</a><a class="auth-btn ghost" href="{{ url_for('download_research_report', report_id=result.standard_report_id, fmt='docx') }}">导出 Word</a>{% else %}<a class="auth-btn ghost" href="{{ url_for('research_report_page') }}">标准报告</a>{% endif %}</div>
  </nav>
  <div class="market-strip">
    <div class="ticker up"><span class="ticker-name">关注标的</span><span class="ticker-value">{{ default_symbol }}</span></div>
    <div class="ticker"><span class="ticker-name">市场</span><span class="ticker-value">{{ default_market }}</span></div>
    <div class="ticker up"><span class="ticker-name">历史记录</span><span class="ticker-value" data-count="history">{{ analysis_history|length }}</span></div>
    <div class="ticker"><span class="ticker-name">缓存数据</span><span class="ticker-value" data-count="cache">{{ cache_count }}</span></div>
    <div class="ticker down"><span class="ticker-name">风险状态</span><span class="ticker-value">监控中</span></div>
  </div>
  <div class="shell">
    <section class="layout">
      <aside class="side-rail" aria-label="工作区导航">
        <a class="rail-link {% if module_view == 'analysis' %}active{% endif %}" href="{{ url_for('analysis_page') }}">分析台</a>
        <a class="rail-link" href="{{ url_for('index') }}#result-panel">结果</a>
        <a class="rail-link {% if module_view == 'holdings' %}active{% endif %}" href="{{ url_for('portfolio_page') }}">持仓</a>
        <a class="rail-link {% if module_view == 'alerts' %}active{% endif %}" href="{{ url_for('alerts_page') }}">价格预警</a>
        <a class="rail-link {% if module_view == 'automation' %}active{% endif %}" href="{{ url_for('automation_page') }}">自动化</a>
        <a class="rail-link {% if module_view == 'history' %}active{% endif %}" href="{{ url_for('analysis_history_page') }}">历史复盘</a>
        <a class="rail-link" href="{{ url_for('market_report') }}">市场报告</a>
        <a class="rail-link" href="{{ url_for('research_report_page') }}">标准报告</a>
      </aside>
      <div class="stack">
        <aside class="left-rail">
        <div class="panel" id="direct-panel"><div class="panel-head"><div><h2 class="section-title" style="margin:0;">标的参数</h2></div></div><form method="post"><input type="hidden" name="mode" value="analyze"><div class="field"><label for="symbol">标的代码</label><input id="symbol" name="symbol" value="{{ form.symbol }}" placeholder="000300.SH"><div class="muted">沪深300指数</div></div><div class="field"><label for="market">市场</label><select id="market" name="market">{% for item in ['fund','a_stock','us_stock','crypto'] %}<option value="{{ item }}" {% if form.market == item %}selected{% endif %}>{{ {'fund':'基金','a_stock':'A股','us_stock':'美股','crypto':'数字资产'}[item] }}</option>{% endfor %}</select></div><div class="field"><label>基准指数</label><input value="{{ default_symbol }}" placeholder="000300.SH"><div class="muted">沪深300指数</div></div><div class="field"><label for="period">回测区间</label><div class="row-2"><input id="start_date" name="start_date" type="date" value="{{ form.start_date }}"><input id="end_date" name="end_date" type="date" value="{{ form.end_date }}"></div><div class="range-buttons"><button type="button" data-period="1y" data-years="1">近1年</button><button type="button" data-period="3y" data-years="3">近3年</button><button type="button" data-period="5y" data-years="5">近5年</button><button type="button" data-period="max" class="primary">全部</button></div><select id="period" name="period" style="margin-top:8px;">{% for item in ['1mo','3mo','6mo','1y','2y','3y','5y','10y','20y','50y','max'] %}<option value="{{ item }}" {% if form.period == item %}selected{% endif %}>{{ item }}</option>{% endfor %}</select></div><div class="field"><label>交易频率</label><select><option>日频</option><option>周频</option><option>月频</option></select></div><div class="field"><label for="use_ai">AI 分析深度</label><select id="use_ai" name="use_ai"><option value="false" {% if not form.use_ai %}selected{% endif %}>标准</option><option value="true" {% if form.use_ai %}selected{% endif %}>全面</option></select></div><div class="toggle-row"><label>自动刷新数据 <span class="switch on"></span></label><label>包含未上市数据 <span class="switch"></span></label><label>使用最新财报 <span class="switch on"></span></label></div><div class="actions" style="margin-top:12px;"><button class="primary" type="submit" style="width:100%;">刷新数据</button></div></form></div>
          <div class="panel" id="agent-panel"><div class="panel-head"><div><h2>追问报告</h2><div class="muted">让 Agent 补充解释、改写或聚焦某段行情。</div></div><div class="panel-tag">Agent</div></div><form method="post"><input type="hidden" name="mode" value="chat"><div class="field"><label for="prompt">你的请求</label><textarea id="prompt" name="prompt" placeholder="解释这次最大回撤的原因，输出老板速读版">{{ form.prompt }}</textarea></div><div class="actions"><button class="primary" type="submit">发送给 Agent</button></div></form><div class="chip-row" style="margin-top:10px;"><span class="chip" data-prompt="分析 002982 基金，生成标准报告">标准报告</span><span class="chip" data-prompt="把报告改写成老板速读版">老板速读版</span><span class="chip" data-prompt="补充风险提示和异常解释">补充风险</span></div></div>
          <div class="data-card"><strong>数据状态</strong><div class="data-row"><span>数据来源：</span><span>Wind / 聚源</span></div><div class="data-row"><span>更新日期：</span><span>2025-05-23 21:00 <i class="dot-ok"></i></span></div><div class="data-row"><span>数据完整性：</span><span>100%</span></div></div><div class="muted" style="margin-top:22px;">报告 ID：RPT_20250524_153021</div>
        </aside>
        <div class="panel" id="history"><div class="panel-head"><div><h2>历史记录</h2><div class="muted">保存每次分析的代码、市场、周期和图表，方便回看或重跑。</div></div><div class="panel-tag">History</div></div>{% if current_user %}<div class="actions" style="margin-bottom:12px;"><a class="chip nav-chip" href="{{ url_for('export_dataset', dataset='history', fmt='csv') }}">导出 CSV</a><a class="chip nav-chip" href="{{ url_for('export_dataset', dataset='history', fmt='xlsx') }}">导出 Excel</a><a class="chip nav-chip" href="{{ url_for('export_dataset', dataset='history', fmt='pdf') }}">导出 PDF</a></div>{% endif %}{% if analysis_history %}<div class="record-grid history-scroll">{% for item in analysis_history %}<div class="record"><div><div class="record-title">{{ item.symbol }} · {{ item.market or "旧图表" }}</div><div class="record-meta">{{ item.time }} · 最新价 {{ item.latest_price }}{% if item.data_range %} · {{ item.data_range }}{% endif %}</div><div class="record-tags"><span class="record-tag">{{ item.period or "历史" }}</span><span class="record-tag">{{ "AI" if item.use_ai else "快速" }}</span></div></div><div class="holding-actions">{% if item.analysis_image %}<a href="{{ item.analysis_image }}" target="_blank" class="chip">图表</a>{% endif %}{% if item.market and item.period %}<form method="post" class="inline-form"><input type="hidden" name="mode" value="analyze"><input type="hidden" name="symbol" value="{{ item.symbol }}"><input type="hidden" name="market" value="{{ item.market }}"><input type="hidden" name="period" value="{{ item.period }}"><input type="hidden" name="use_ai" value="{{ 'true' if item.use_ai else 'false' }}"><button class="primary tiny-button" type="submit">重跑</button></form>{% endif %}</div></div>{% endfor %}</div>{% else %}<div class="muted">还没有分析历史。跑一次分析后会记录在这里。</div>{% endif %}</div>
        {% if module_view == 'history' and analysis_history %}
        <div class="panel" style="max-width:1280px;margin:12px auto 0;padding:18px;border:1px solid var(--line);border-radius:6px;">
          <div class="panel-head"><div><h2>导出最近投资复盘报告</h2><div class="muted">把最新一条历史分析整理成投资复盘与风险报告，可下载 PDF、Word、Markdown。</div></div></div>
          <div class="actions"><a class="chip primary" href="{{ url_for('download_history_research_report', item_index=0, fmt='pdf') }}">导出 PDF</a><a class="chip" href="{{ url_for('download_history_research_report', item_index=0, fmt='docx') }}">导出 Word</a><a class="chip" href="{{ url_for('download_history_research_report', item_index=0, fmt='md') }}">导出 Markdown</a><a class="chip" href="{{ url_for('research_report_page') }}">全部复盘报告</a></div>
        </div>
        {% endif %}
        <div class="module-launcher">
          <a class="module-card" href="{{ url_for('portfolio_page') }}"><strong>持仓管理</strong><span>添加、移除、导出持仓，并从组合视角发起单标的分析。</span><em>进入持仓 →</em></a>
          <a class="module-card" href="{{ url_for('alerts_page') }}"><strong>价格预警</strong><span>设置到价提醒，检查价格触发和均线突破状态。</span><em>进入预警 →</em></a>
          <a class="module-card" href="{{ url_for('automation_page') }}"><strong>自动化任务</strong><span>配置每日扫描、摘要日报、预警检查和系统维护。</span><em>进入自动化 →</em></a>
          <a class="module-card" href="{{ url_for('analysis_history_page') }}"><strong>历史复盘</strong><span>查看过往分析、图表和重跑入口，支持导出记录。</span><em>进入历史 →</em></a>
        </div>
        <div class="panel" id="holdings-panel">
          {% set ns = namespace(total_cost=0, fund_count=0, stock_count=0, crypto_count=0, max_cost=0) %}
          {% for h in holdings %}
            {% set row_cost = (h.quantity|float) * (h.avg_cost|float) %}
            {% set ns.total_cost = ns.total_cost + row_cost %}
            {% if row_cost > ns.max_cost %}{% set ns.max_cost = row_cost %}{% endif %}
            {% if h.market == 'fund' %}{% set ns.fund_count = ns.fund_count + 1 %}{% endif %}
            {% if h.market == 'a_stock' or h.market == 'us_stock' %}{% set ns.stock_count = ns.stock_count + 1 %}{% endif %}
            {% if h.market == 'crypto' %}{% set ns.crypto_count = ns.crypto_count + 1 %}{% endif %}
          {% endfor %}
          {% set concentration = (ns.max_cost / ns.total_cost * 100) if ns.total_cost else 0 %}
          <div class="portfolio-head">
            <div>
              <h2>组合诊断</h2>
              <div class="muted">从持仓结构、集中度、资产类型和报告动作四个角度管理组合，不再和历史复盘混在一起。</div>
            </div>
            <div class="portfolio-actions">
              {% if current_user %}
              <a class="chip nav-chip" href="{{ url_for('export_dataset', dataset='holdings', fmt='xlsx') }}">导出 Excel</a>
              <a class="chip nav-chip" href="{{ url_for('export_dataset', dataset='holdings', fmt='pdf') }}">导出 PDF</a>
              {% endif %}
              <a class="chip nav-chip" href="{{ url_for('research_report_page') }}">生成标准报告</a>
            </div>
          </div>
          <div class="portfolio-kpis">
            <div class="portfolio-kpi"><span>持仓数量</span><strong>{{ holdings|length }}</strong></div>
            <div class="portfolio-kpi"><span>估算成本</span><strong>{{ "%.2f"|format(ns.total_cost) }}</strong></div>
            <div class="portfolio-kpi"><span>最大单项占比</span><strong>{{ "%.1f%%"|format(concentration) }}</strong></div>
            <div class="portfolio-kpi"><span>资产类型</span><strong>{{ ns.fund_count + ns.stock_count + ns.crypto_count }}</strong></div>
          </div>
          <div class="diagnosis-grid">
            <div class="diagnosis-card"><div class="diagnosis-score {% if concentration >= 50 %}danger{% elif concentration >= 30 %}warn{% endif %}">集中度</div><b>{% if concentration >= 50 %}偏高{% elif concentration >= 30 %}中等{% else %}可控{% endif %}</b><span>最大单项持仓约占 {{ "%.1f%%"|format(concentration) }}，超过 30% 时建议在报告中提示集中度风险。</span></div>
            <div class="diagnosis-card"><div class="diagnosis-score">资产分布</div><b>基金 {{ ns.fund_count }} / 股票 {{ ns.stock_count }} / 数字资产 {{ ns.crypto_count }}</b><span>后续可接入基准、行业和风格暴露，生成更完整的组合诊断报告。</span></div>
            <div class="diagnosis-card"><div class="diagnosis-score warn">Agent 建议</div><b>先做复盘，再做决策</b><span>当前模块定位为组合分析和风险报告，不连接券商执行。</span></div>
          </div>
          <div class="portfolio-grid">
            <form class="portfolio-card" method="post" action="#holdings-panel">
              <input type="hidden" name="mode" value="holding_add">
              <h3>添加持仓</h3>
              <div class="field"><label for="holding_symbol">代码</label><input id="holding_symbol" name="holding_symbol" placeholder="例如 002982"></div>
              <div class="field"><label for="holding_market">市场</label><select id="holding_market" name="holding_market">{% for item in ['fund','a_stock','us_stock','crypto'] %}<option value="{{ item }}">{{ {'fund':'基金','a_stock':'A股','us_stock':'美股','crypto':'数字资产'}[item] }}</option>{% endfor %}</select></div>
              <div class="row-2"><div class="field"><label for="holding_qty">数量</label><input id="holding_qty" name="holding_qty" placeholder="例如 3000"></div><div class="field"><label for="holding_cost">成本</label><input id="holding_cost" name="holding_cost" placeholder="例如 0.8599"></div></div>
              <div class="field"><label for="holding_date">买入日期</label><input id="holding_date" name="holding_date" placeholder="例如 2025-04-25"></div>
              <button class="primary" type="submit" style="width:100%;">保存持仓</button>
            </form>
            <div class="portfolio-table-wrap">
              {% if holdings %}
              <table>
                <thead><tr><th>代码</th><th>市场</th><th>数量</th><th>成本</th><th>估算成本</th><th>操作</th></tr></thead>
                <tbody>
                  {% for h in holdings %}
                  {% set row_cost = (h.quantity|float) * (h.avg_cost|float) %}
                  <tr>
                    <td><b>{{ h.symbol }}</b></td>
                    <td>{{ h.market }}</td>
                    <td>{{ h.quantity }}</td>
                    <td>{{ "%.4f"|format(h.avg_cost) }}</td>
                    <td>{{ "%.2f"|format(row_cost) }}</td>
                    <td>
                      <div class="holding-actions">
                        <form method="post"><input type="hidden" name="mode" value="analyze"><input type="hidden" name="symbol" value="{{ h.symbol }}"><input type="hidden" name="market" value="{{ h.market }}"><input type="hidden" name="period" value="max"><input type="hidden" name="use_ai" value="false"><button class="primary tiny-button" type="submit">分析</button></form>
                        <form method="post" action="#holdings-panel"><input type="hidden" name="mode" value="holding_remove"><input type="hidden" name="holding_symbol" value="{{ h.symbol }}"><input type="hidden" name="holding_market" value="{{ h.market }}"><button class="ghost tiny-button" type="submit">移除</button></form>
                      </div>
                    </td>
                  </tr>
                  {% endfor %}
                </tbody>
              </table>
              {% else %}
              <div class="empty-portfolio"><strong>还没有持仓记录</strong><span>先添加一个基金、股票或数字资产，系统会在这里生成组合诊断入口。</span></div>
              {% endif %}
            </div>
          </div>
        </div>
        <div class="panel" id="alerts-panel"><div class="panel-head"><div><h2>价格预警</h2><div class="muted">设置到价提醒，并结合自动扫描检查价格触发和均线突破。</div></div><div class="panel-tag">Alerts</div></div><form method="post" action="#alerts-panel"><input type="hidden" name="mode" value="alert_add"><div class="row-2"><div class="field"><label for="alert_symbol">代码</label><input id="alert_symbol" name="alert_symbol" placeholder="例如 002982"></div><div class="field"><label for="alert_market">市场</label><select id="alert_market" name="alert_market">{% for item in ['fund','a_stock','us_stock','crypto'] %}<option value="{{ item }}">{{ {'fund':'基金','a_stock':'A股','us_stock':'美股','crypto':'数字资产'}[item] }}</option>{% endfor %}</select></div></div><div class="row-2"><div class="field"><label for="alert_condition">条件</label><select id="alert_condition" name="alert_condition"><option value="lte">跌到/低于</option><option value="gte">涨到/高于</option></select></div><div class="field"><label for="alert_target_price">目标价</label><input id="alert_target_price" name="alert_target_price" placeholder="例如 0.8500"></div></div><div class="actions"><button class="secondary" type="submit">添加预警</button><button class="ghost tiny-button" type="submit" name="mode" value="alert_check">立即检查</button>{% if current_user %}<a class="chip nav-chip" href="{{ url_for('export_dataset', dataset='alerts', fmt='xlsx') }}">导出预警</a>{% endif %}</div></form><div class="subtle-card" style="margin-top:16px;">{% if alerts %}<table><thead><tr><th>代码</th><th>条件</th><th>目标价</th><th>状态</th><th>操作</th></tr></thead><tbody>{% for alert in alerts %}<tr><td>{{ alert.symbol }}<div class="record-meta">{{ {'fund':'基金','a_stock':'A股','us_stock':'美股','crypto':'数字资产'}.get(alert.market, alert.market) }}</div></td><td>{{ "≤" if alert.condition == "lte" else "≥" }}</td><td>{{ "%.4f"|format(alert.target_price) }}</td><td>{{ "已触发" if alert.last_triggered_at else "监控中" }}</td><td><form method="post" action="#alerts-panel"><input type="hidden" name="mode" value="alert_remove"><input type="hidden" name="alert_id" value="{{ alert.id }}"><button class="ghost tiny-button" type="submit">删除</button></form></td></tr>{% endfor %}</tbody></table>{% else %}<div class="muted">还没有价格预警。</div>{% endif %}</div></div>
        <div class="panel" id="automation-panel"><div class="panel-head"><div><h2>自动化</h2><div class="muted">每天定时扫描持仓、生成日报，按分钟检查价格预警，并自动维护任务、备份和日志。</div></div><div class="panel-tag">Automation</div></div>{% set daily_scan = (automations | selectattr('job_type','equalto','daily_holdings_scan') | list | first) %}{% set daily_digest = (automations | selectattr('job_type','equalto','daily_digest') | list | first) %}{% set price_scan = (automations | selectattr('job_type','equalto','price_alert_scan') | list | first) %}{% set maintenance = (automations | selectattr('job_type','equalto','system_maintenance') | list | first) %}<form method="post" action="#automation-panel"><input type="hidden" name="mode" value="automation_save"><div class="field"><label for="automation_time">每日执行时间</label><input id="automation_time" name="automation_time" value="{{ daily_scan.run_time if daily_scan else '09:00' }}"></div><label><input type="checkbox" name="daily_scan_enabled" {% if daily_scan and daily_scan.enabled %}checked{% endif %} style="width:auto;margin-right:8px;">每天自动分析持仓</label><label><input type="checkbox" name="daily_digest_enabled" {% if daily_digest and daily_digest.enabled %}checked{% endif %} style="width:auto;margin-right:8px;">每天自动生成摘要日报</label><label><input type="checkbox" name="price_scan_enabled" {% if price_scan and price_scan.enabled %}checked{% endif %} style="width:auto;margin-right:8px;">定时检查价格预警与均线突破</label><div class="field"><label for="alert_interval_minutes">预警检查间隔（分钟）</label><input id="alert_interval_minutes" name="alert_interval_minutes" value="{{ price_scan.interval_minutes if price_scan else 15 }}"></div><label><input type="checkbox" name="maintenance_enabled" {% if maintenance and maintenance.enabled %}checked{% endif %} style="width:auto;margin-right:8px;">自动维护任务、备份和日志</label><div class="field"><label for="maintenance_interval_minutes">维护间隔（分钟）</label><input id="maintenance_interval_minutes" name="maintenance_interval_minutes" value="{{ maintenance.interval_minutes if maintenance else 60 }}"></div><div class="actions"><button class="secondary" type="submit">保存自动化</button><button class="ghost tiny-button" type="submit" name="mode" value="automation_run">立即扫描</button><button class="ghost tiny-button" type="submit" name="mode" value="automation_run" formaction="#automation-panel" onclick="this.form.job_type.value='system_maintenance'">立即维护</button><input type="hidden" name="job_type" value="daily_holdings_scan"></div></form><div class="subtle-card" style="margin-top:16px;"><div class="muted" style="margin-bottom:10px;">最近自动化日志</div>{% if automation_log %}<div class="record-grid">{% for item in automation_log[:5] %}<div class="record"><div><div class="record-title">{{ item.type }}</div><div class="record-meta">{{ item.time }}</div></div></div>{% endfor %}</div>{% else %}<div class="muted">还没有自动化运行记录。</div>{% endif %}</div></div>
      </div>
      <main class="report-main">
        <div class="panel result-panel" id="result-panel">{% if error %}<div class="notice error">{{ error }}</div>{% endif %}{% if note %}<div class="notice">{{ note }}</div>{% endif %}
          <div class="section-title">标行摘要</div>
          <div class="summary-box"><strong>{% if result %}标的摘要</strong><div>当前报告已完成数据计算与图表生成。请重点关注收益表现、最大回撤、样本区间和 AI 解读中的风险措辞。</div>{% else %}标的摘要</strong><div class="muted">左侧选择报告对象和数据区间后生成报告。这里会展示摘要、核心指标、图表和完整 Markdown。</div>{% endif %}</div>
          <div class="section-title">核心指标</div>
          {% if result %}<div class="kpis"><div class="kpi"><span>标的</span><strong>{{ result.symbol }}</strong></div><div class="kpi"><span>市场</span><strong>{{ result.market }}</strong></div><div class="kpi"><span>周期</span><strong>{{ result.period }}</strong></div><div class="kpi"><span>最新价格</span><strong>{{ result.latest_price }}</strong></div><div class="kpi"><span>数据区间</span><strong>{{ result.data_range }}</strong></div><div class="kpi"><span>样本数</span><strong>{{ result.data_points }}</strong></div></div>{% else %}<div class="kpis"><div class="kpi"><span>年化收益</span><strong>13.72%</strong></div><div class="kpi"><span>超额收益</span><strong>6.38%</strong></div><div class="kpi"><span>夏普比率</span><strong title="单位波动带来的超额收益">0.88</strong></div><div class="kpi"><span>最大回撤</span><strong>18.35%</strong></div><div class="kpi"><span>胜率</span><strong>57.62%</strong></div><div class="kpi"><span>跟踪误差</span><strong>6.21%</strong></div></div>{% endif %}
          <div class="section-title">信号 / 因子矩阵</div>
          <div class="metric-table"><table><thead><tr><th>因子类别</th><th>因子名称</th><th>方向</th><th>IC 均值</th><th>IC_IR</th><th>多头暴露</th><th>空头暴露</th><th>结论</th></tr></thead><tbody><tr><td>价值</td><td>市盈率 PE</td><td>负</td><td class="neg">-0.045</td><td>-1.23</td><td>-0.21</td><td>0.32</td><td>弱有效</td></tr><tr><td>成长</td><td>营收增速 TTM</td><td>正</td><td class="pos">0.042</td><td>1.35</td><td>0.27</td><td>-0.26</td><td>有效</td></tr><tr><td>质量</td><td>ROE TTM</td><td>正</td><td class="pos">0.046</td><td>1.28</td><td>0.34</td><td>-0.31</td><td>有效</td></tr><tr><td>动量</td><td>20日价格动量</td><td>正</td><td class="pos">0.036</td><td>1.10</td><td>0.23</td><td>-0.21</td><td>观察</td></tr><tr><td>情绪</td><td>成交量异动</td><td>正</td><td>0.033</td><td>0.98</td><td>0.19</td><td>-0.17</td><td>观察</td></tr></tbody></table></div>
          <div class="section-title">历史表现复盘</div>
          <div class="report-grid-2"><div class="mini-chart"><svg viewBox="0 0 720 260" preserveAspectRatio="none"><rect width="720" height="260" fill="#fff"/><g stroke="#edf1f5"><path d="M45 30H700M45 80H700M45 130H700M45 180H700M45 230H700"/><path d="M120 20V235M220 20V235M320 20V235M420 20V235M520 20V235M620 20V235"/></g><path d="M45 190 C90 170 115 155 150 165 S220 110 260 122 S320 104 365 80 S450 72 505 58 S590 45 700 34" fill="none" stroke="#2563eb" stroke-width="3"/><path d="M45 200 C100 180 135 170 175 176 S240 150 300 158 S360 132 430 124 S560 110 700 92" fill="none" stroke="#f59e0b" stroke-width="2"/><path d="M45 225 C160 220 250 212 360 200 S540 182 700 150" fill="none" stroke="#93c5fd" stroke-width="2"/><text x="52" y="26" fill="#667085" font-size="12">策略净值 / 基准净值 / 超额收益</text></svg></div><div class="metric-table"><table><thead><tr><th>指标</th><th>策略</th><th>基准</th><th>超额</th></tr></thead><tbody><tr><td>累计收益</td><td>179.62%</td><td>97.71%</td><td>81.91%</td></tr><tr><td>年化收益</td><td>13.72%</td><td>7.34%</td><td>6.38%</td></tr><tr><td>年化波动率</td><td>15.65%</td><td>18.31%</td><td>-</td></tr><tr><td>夏普比率</td><td>0.88</td><td>0.48</td><td>-</td></tr><tr><td>最大回撤</td><td class="neg">18.35%</td><td>28.76%</td><td class="pos">-10.41%</td></tr><tr><td>胜率</td><td>57.62%</td><td>-</td><td>-</td></tr></tbody></table></div></div>
          <div class="section-title">归因分析 / 月度收益</div>
          <div class="report-grid-2"><div class="metric-table"><table><thead><tr><th>归因项</th><th>配置效应</th><th>选股效应</th><th>交互效应</th><th>合计超额</th></tr></thead><tbody><tr><td>行业</td><td class="bar-cell"><div class="bar"><i style="width:26%"></i></div>0.73%</td><td>3.21%</td><td>0.12%</td><td><b>4.06%</b></td></tr><tr><td>风格</td><td>0.51%</td><td>1.87%</td><td>0.08%</td><td><b>2.46%</b></td></tr><tr><td>个股</td><td>0.00%</td><td>-0.23%</td><td>0.02%</td><td class="neg">-0.21%</td></tr></tbody></table></div><div class="metric-table"><table><thead><tr><th>年度</th><th>1月</th><th>2月</th><th>3月</th><th>4月</th><th>5月</th><th>年度</th></tr></thead><tbody><tr><td>2025</td><td class="heat pos">2.31</td><td class="heat neg">-1.02</td><td class="heat pos">1.45</td><td class="heat pos">0.89</td><td class="heat pos">1.15</td><td>4.84</td></tr><tr><td>2024</td><td class="heat neg">-1.27</td><td class="heat pos">2.11</td><td class="heat neg">-0.76</td><td class="heat pos">1.35</td><td class="heat neg">-0.34</td><td>9.40</td></tr><tr><td>2023</td><td class="heat pos">0.82</td><td class="heat neg">-0.59</td><td class="heat pos">1.32</td><td class="heat neg">-0.27</td><td class="heat pos">0.91</td><td>4.86</td></tr></tbody></table></div></div>
          <div class="section-title">Agent 结论</div>
          <div class="agent-card" data-followup-card><div><strong>自动摘要与审校</strong><span class="muted" data-followup-context>过去表现需要和风险一起看。当前报告用于复盘和识别风险，下一步应重点观察回撤是否扩大、数据是否完整、持仓是否过于集中。</span></div><button type="button" class="chip followup-toggle">追问这段</button><div class="followup-box"><textarea class="followup-question" rows="3" placeholder="继续追问：例如如果继续跌我可能承受什么？这段改成小资金账户版？"></textarea><div class="actions"><button type="button" class="primary followup-send">发送追问</button></div><div class="followup-output"></div></div></div>
        </div>
      </main>
      <aside class="right-rail">
        <section><div class="panel-head"><div><h2>复盘 / 报告假设</h2><div class="muted">用于解释报告口径，不代表下单或自动执行设置。</div></div><div class="panel-tag">Assumptions</div></div><div class="assumption-list"><div><b>报告对象</b><span>个人持仓 / 基金 / ETF / 股票</span></div><div><b>基准口径</b><span>{{ default_symbol }}</span></div><div><b>观察来源</b><span>行情 + 持仓 + 净值/交易记录</span></div><div><b>复盘口径</b><span>日频观察</span></div><div><b>成本假设</b><span>系统默认</span></div><div><b>AI 解读</b><span>{{ "开启" if form.use_ai else "按需" }}</span></div></div></section>
        <section style="margin-top:18px;"><div class="panel-head"><div><h2>风险评价阈值</h2><div class="muted">报告风控口径，只用于提醒和复核。</div></div><div class="risk-badge">中等风险</div></div><div class="check-list"><div><b>最大回撤阈值</b><span>20.00%</span></div><div><b>单日最大亏损</b><span>3.00%</span></div><div><b>行业最大暴露</b><span>15.00%</span></div><div><b>单项持仓上限</b><span>30.00%</span></div><div><b>频繁交易提醒</b><span>开启</span></div></div></section>
        <section style="margin-top:18px;"><div class="panel-head"><div><h2>AI 审校状态</h2><div class="muted">导出前检查项。</div></div></div><div class="check-list"><div><b>数据一致性</b><span class="pos">通过</span></div><div><b>资料依据</b><span class="pos">已标注</span></div><div><b>风险提示</b><span class="pos">已补充</span></div><div><b>买卖指令检查</b><span>已规避</span></div></div></section>
        <section style="margin-top:18px;"><div class="panel-head"><div><h2>读者版本</h2><div class="muted">一键切换报告表达口径。</div></div></div><div class="reader-switch"><button type="button" class="chip active" data-reader="个人投资者版">个人投资者版</button><button type="button" class="chip" data-reader="小资金账户版">小资金账户版</button><button type="button" class="chip" data-reader="业余量化版">业余量化版</button><button type="button" class="chip" data-reader="小型投研团队版">小型投研团队版</button></div><div class="reader-note" id="readerNote">个人投资者版：用通俗语言解释过去表现、近期变化、回撤风险和下一步观察清单。</div></section>
        <section style="margin-top:18px;"><div class="panel-head"><div><h2>导出与分享</h2><div class="muted">报告交付动作。</div></div></div><div class="export-list">{% if result and result.standard_report_id %}<a class="primary" href="{{ url_for('download_research_report', report_id=result.standard_report_id, fmt='pdf') }}">导出 PDF</a><a href="{{ url_for('download_research_report', report_id=result.standard_report_id, fmt='docx') }}">导出 Word</a><a href="{{ url_for('download_research_report', report_id=result.standard_report_id, fmt='md') }}">导出 Markdown</a>{% else %}<a class="primary" href="{{ url_for('research_report_page') }}">导出 PDF</a><a href="{{ url_for('export_dataset', dataset='history', fmt='xlsx') }}">导出 Excel</a><button type="button" class="js-save-report">保存报告配置</button><button type="button" class="js-share-report">分享报告链接</button>{% endif %}</div><div class="action-feedback" id="reportActionFeedback" hidden></div></section>
      </aside>
      <footer class="workflow" aria-label="生成流程时间线"><div class="workflow-title">分析流程（时间线）</div><div class="step"><b>1</b><span>数据准备</span><small>2025-05-24 14:10</small></div><div class="step"><b>2</b><span>因子计算</span><small>14:18</small></div><div class="step"><b>3</b><span>因子筛选</span><small>14:25</small></div><div class="step"><b>4</b><span>组合构建</span><small>14:32</small></div><div class="step"><b>5</b><span>回测执行</span><small>14:45</small></div><div class="step"><b>6</b><span>归因分析</span><small>14:58</small></div><div class="step"><b>7</b><span>风险评估</span><small>15:10</small></div><div class="step"><b>8</b><span>报告生成</span><small>15:30</small></div><div class="workflow-status"><span>总耗时：1小时20分 <i class="dot-ok"></i> 成功</span><a class="chip" href="{{ url_for('analysis_history_page') }}">查看日志</a></div></footer>
    </section>
  </div>
  <div class="explain-modal" id="explainModal" role="dialog" aria-modal="true" aria-labelledby="explainTitle">
    <div class="explain-dialog">
      <div class="explain-head"><strong id="explainTitle">指标解释</strong><button type="button" class="explain-close" aria-label="关闭">×</button></div>
      <div class="explain-body" id="explainBody">正在加载...</div>
    </div>
  </div>
  <script>
    document.querySelectorAll('.chip[data-prompt]').forEach(chip => chip.addEventListener('click', () => { const box = document.getElementById('prompt'); if (box) { box.value = chip.dataset.prompt || ''; box.focus(); } }));
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');
    const periodSelect = document.getElementById('period');
    const formatDate = (date) => date.toISOString().slice(0, 10);
    document.querySelectorAll('.range-buttons button[data-period]').forEach(button => button.addEventListener('click', () => {
      document.querySelectorAll('.range-buttons button[data-period]').forEach(item => item.classList.toggle('primary', item === button));
      if (periodSelect) periodSelect.value = button.dataset.period || 'max';
      if (!startDateInput || !endDateInput) return;
      if (!button.dataset.years) {
        startDateInput.value = '';
        endDateInput.value = '';
        return;
      }
      const end = new Date();
      const start = new Date(end);
      start.setFullYear(start.getFullYear() - Number(button.dataset.years || 0));
      startDateInput.value = formatDate(start);
      endDateInput.value = formatDate(end);
    }));
    document.querySelectorAll('form').forEach(form => form.addEventListener('submit', () => { const mode = form.querySelector('[name="mode"]')?.value || ''; if (['analyze','chat'].includes(mode)) document.getElementById('submitOverlay')?.classList.add('active'); }));
    const csrfToken = '{{ csrf_token() }}';
    const postJson = async (url, payload) => {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
        body: JSON.stringify(payload || {})
      });
      const data = await res.json().catch(() => ({ ok:false, error:'服务返回格式异常。' }));
      if (!res.ok || !data.ok) throw new Error(data.error || '操作失败。');
      return data;
    };
    const collectReportPayload = () => {
      const toggles = {};
      document.querySelectorAll('.toggle-row label').forEach(label => {
        toggles[label.textContent.trim()] = Boolean(label.querySelector('.switch')?.classList.contains('on'));
      });
      return {
        page: window.location.pathname + window.location.search,
        title: document.querySelector('.report-title h1')?.textContent.trim() || document.title,
        reader_version: document.querySelector('[data-reader].active')?.dataset.reader || '个人投资者版',
        toggles,
        form: {
          symbol: document.getElementById('symbol')?.value || '',
          market: document.getElementById('market')?.value || '',
          period: document.getElementById('period')?.value || '',
          start_date: document.getElementById('start_date')?.value || '',
          end_date: document.getElementById('end_date')?.value || '',
          use_ai: document.getElementById('use_ai')?.value || ''
        }
      };
    };
    const explainModal = document.getElementById('explainModal');
    const explainTitle = document.getElementById('explainTitle');
    const explainBody = document.getElementById('explainBody');
    const closeExplain = () => explainModal?.classList.remove('active');
    const explainTargets = [
      ...document.querySelectorAll('#result-panel .kpi span'),
      ...document.querySelectorAll('#result-panel .metric-table th'),
      ...document.querySelectorAll('#result-panel .metric-table td:first-child'),
      ...document.querySelectorAll('.right-rail .assumption-list b'),
      ...document.querySelectorAll('.right-rail .check-list b')
    ];
    document.querySelectorAll('#result-panel .metric-table table').forEach(table => {
      const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent.trim());
      const factorNameIndex = headers.indexOf('因子名称');
      if (factorNameIndex >= 0) {
        table.querySelectorAll(`tbody tr td:nth-child(${factorNameIndex + 1})`).forEach(cell => explainTargets.push(cell));
      }
    });
    const makeExplainButton = (node) => {
      const name = (node.textContent || '').trim();
      if (!name || node.querySelector?.('.explain-button')) return;
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'explain-button';
      button.dataset.explain = name;
      button.textContent = name;
      node.textContent = '';
      node.appendChild(button);
    };
    explainTargets.forEach(makeExplainButton);
    document.querySelectorAll('[data-explain]').forEach(button => button.addEventListener('click', async () => {
      const name = button.dataset.explain || button.textContent.trim();
      if (explainTitle) explainTitle.textContent = name;
      if (explainBody) explainBody.textContent = '正在加载...';
      explainModal?.classList.add('active');
      try {
        const data = await fetch(`/api/ui/explain?name=${encodeURIComponent(name)}`).then(r => r.json());
        if (!data.ok) throw new Error(data.error || '解释加载失败。');
        if (explainBody) explainBody.textContent = data.explanation;
      } catch (err) {
        if (explainBody) explainBody.textContent = err.message || '解释加载失败。';
      }
    }));
    document.querySelector('.explain-close')?.addEventListener('click', closeExplain);
    explainModal?.addEventListener('click', (event) => {
      if (event.target === explainModal) closeExplain();
    });
    window.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') closeExplain();
    });
    document.querySelectorAll('[data-chart-tabs] button').forEach(button => button.addEventListener('click', async () => {
      document.querySelectorAll('[data-chart-tabs] button').forEach(item => item.classList.toggle('active', item === button));
      const range = button.dataset.range || button.textContent.trim();
      const chart = document.getElementById('dashboardEquityChart');
      const portfolioReturn = document.getElementById('portfolioReturn');
      const benchmarkReturn = document.getElementById('benchmarkReturn');
      try {
        const preset = await fetch(`/api/ui/dashboard_returns?range=${encodeURIComponent(range)}`).then(r => r.json());
        if (!preset.ok) throw new Error(preset.error || '收益区间读取失败。');
        if (portfolioReturn) portfolioReturn.textContent = preset.portfolio_return;
        if (benchmarkReturn) benchmarkReturn.textContent = preset.benchmark_return;
        if (chart) chart.innerHTML = `<path d="${preset.portfolio_path}" fill="none" stroke="#0aa3a3" stroke-width="4"/><path d="${preset.benchmark_path}" fill="none" stroke="#2684ff" stroke-width="3"/>`;
      } catch (err) {
        button.title = err.message || '收益区间读取失败。';
      }
    }));
    const actionFeedback = document.getElementById('reportActionFeedback');
    const showActionFeedback = (text) => {
      if (!actionFeedback) return;
      actionFeedback.hidden = false;
      actionFeedback.textContent = text;
    };
    document.querySelectorAll('.js-save-report').forEach(button => button.addEventListener('click', async () => {
      try {
        const data = await postJson('{{ url_for("save_report_config_api") }}', collectReportPayload());
        showActionFeedback(data.message || '已保存当前报告配置。');
      } catch (err) {
        showActionFeedback(err.message || '保存失败，请先登录后重试。');
      }
    }));
    document.querySelectorAll('.js-share-report').forEach(button => button.addEventListener('click', async () => {
      try {
        const data = await postJson('{{ url_for("share_report_link_api") }}', collectReportPayload());
        const link = data.share_url;
        await navigator.clipboard.writeText(link);
        showActionFeedback(`分享链接已复制：${link}`);
      } catch (err) {
        showActionFeedback(err.message || '分享链接生成失败，请先登录后重试。');
      }
    }));
    const readerFallbacks = {
      '个人投资者版': {
        note: '个人投资者版：用通俗语言解释过去表现、近期变化、回撤风险和下一步观察清单。',
        conclusion: '过去表现需要和风险一起看。当前报告用于复盘和识别风险，下一步应重点观察回撤是否扩大、数据是否完整、持仓是否过于集中。'
      },
      '小资金账户版': {
        note: '小资金账户版：重点看仓位是否过重、继续下跌能否承受、手续费和频繁交易是否影响收益。',
        conclusion: '小资金账户应优先控制试错成本。先复核单一持仓占比、继续下跌时的可承受亏损，以及交易成本是否会吞掉收益。'
      },
      '业余量化版': {
        note: '业余量化版：保留收益、回撤、波动、样本区间和参数观察，但明确只是复核工具。',
        conclusion: '参数和观察信号只用于研究复核，不能理解为收益保证或交易规则。下一步应做样本外验证、回撤区间复盘和参数敏感性检查。'
      },
      '小型投研团队版': {
        note: '小型投研团队版：强调数据来源、资料引用、风险边界和可追溯复盘流程。',
        conclusion: '报告适合作为复盘底稿：保留数据来源、风险解释和观察清单，避免写成直接买卖建议。'
      }
    };
    const applyReaderVersion = (version, payload) => {
      const preset = payload || readerFallbacks[version] || readerFallbacks['个人投资者版'];
      const note = document.getElementById('readerNote');
      const conclusion = document.querySelector('[data-followup-context]');
      if (note) note.textContent = preset.note || '';
      if (conclusion) conclusion.textContent = preset.conclusion || conclusion.textContent;
    };
    document.querySelectorAll('[data-reader]').forEach(button => button.addEventListener('click', async () => {
      document.querySelectorAll('[data-reader]').forEach(item => item.classList.toggle('active', item === button));
      applyReaderVersion(button.dataset.reader);
      try {
        const data = await postJson('{{ url_for("reader_version_api") }}', { version: button.dataset.reader });
        applyReaderVersion(button.dataset.reader, data);
      } catch (err) {
        const note = document.getElementById('readerNote');
        if (note) note.textContent = err.message || '读者版本保存失败，请先登录后重试。';
      }
    }));
    document.querySelectorAll('.toggle-row label').forEach(label => label.addEventListener('click', async (event) => {
      if (event.target.tagName === 'INPUT') return;
      label.querySelector('.switch')?.classList.toggle('on');
      try {
        await postJson('{{ url_for("save_report_config_api") }}', collectReportPayload());
      } catch (err) {
        showActionFeedback(err.message || '开关状态保存失败，请先登录后重试。');
      }
    }));
    function appendFollowupMessage(box, text, cls) {
      const node = document.createElement('div');
      node.className = `followup-message ${cls || ''}`.trim();
      node.textContent = text;
      box.appendChild(node);
      box.scrollTop = box.scrollHeight;
    }
    document.querySelectorAll('[data-followup-card]').forEach(card => {
      const panel = card.querySelector('.followup-box');
      const output = card.querySelector('.followup-output');
      const textarea = card.querySelector('.followup-question');
      const contextNode = card.querySelector('[data-followup-context]');
      card.querySelector('.followup-toggle')?.addEventListener('click', () => {
        panel?.classList.toggle('active');
        textarea?.focus();
      });
      card.querySelector('.followup-send')?.addEventListener('click', async () => {
        const question = (textarea?.value || '').trim();
        if (!question) return;
        appendFollowupMessage(output, question, 'user');
        textarea.value = '';
        const waiting = 'Agent 正在分析...';
        appendFollowupMessage(output, waiting, '');
        const waitingNode = output.lastElementChild;
        const formData = new FormData();
        formData.append('csrf_token', '{{ csrf_token() }}');
        formData.append('question', question);
        formData.append('context', contextNode?.textContent || '');
        try {
          const res = await fetch('{{ url_for("report_followup_api") }}', { method:'POST', body:formData });
          const data = await res.json();
          waitingNode.textContent = data.ok ? data.answer : (data.error || '追问失败，请稍后重试。');
        } catch (err) {
          waitingNode.textContent = '追问失败，请检查 API 配置或稍后重试。';
        }
      });
    });
    function drawEquityChart() {
      const svg = document.getElementById('equityChart');
      const equityNode = document.getElementById('equityData');
      const benchmarkNode = document.getElementById('benchmarkData');
      if (!svg || !equityNode) return;
      const equity = JSON.parse(equityNode.textContent || '[]');
      const benchmark = benchmarkNode ? JSON.parse(benchmarkNode.textContent || '[]') : [];
      const series = [
        { name: '策略', color: '#0e7490', points: equity },
        { name: '买入持有', color: '#b45309', points: benchmark }
      ].filter(s => s.points.length);
      if (!series.length) {
        svg.innerHTML = '<text x="50%" y="50%" text-anchor="middle" fill="#64748b">暂无策略曲线数据</text>';
        return;
      }
      const width = Math.max(svg.clientWidth || 720, 320);
      const height = Math.max(svg.clientHeight || 420, 280);
      const pad = { left: 58, right: 20, top: 28, bottom: 48 };
      const allValues = series.flatMap(s => s.points.map(p => Number(p.value))).filter(Number.isFinite);
      const minValue = Math.min(...allValues);
      const maxValue = Math.max(...allValues);
      const span = Math.max(maxValue - minValue, 1);
      const xMax = Math.max(...series.map(s => s.points.length - 1), 1);
      const x = (i) => pad.left + (i / xMax) * (width - pad.left - pad.right);
      const y = (v) => pad.top + ((maxValue - v) / span) * (height - pad.top - pad.bottom);
      const grid = [0, 0.25, 0.5, 0.75, 1].map(t => {
        const yy = pad.top + t * (height - pad.top - pad.bottom);
        const val = maxValue - t * span;
        return `<line x1="${pad.left}" y1="${yy}" x2="${width - pad.right}" y2="${yy}" stroke="#e5e7eb"/><text x="10" y="${yy + 4}" fill="#64748b" font-size="12">${Math.round(val).toLocaleString()}</text>`;
      }).join('');
      const paths = series.map(s => {
        const d = s.points.map((p, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(Number(p.value)).toFixed(1)}`).join(' ');
        return `<path d="${d}" fill="none" stroke="${s.color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>`;
      }).join('');
      const legend = series.map((s, i) => `<g transform="translate(${pad.left + i * 110},${height - 18})"><rect width="12" height="12" rx="3" fill="${s.color}"/><text x="18" y="11" fill="#334155" font-size="13">${s.name}</text></g>`).join('');
      const firstDate = series[0].points[0]?.date || '';
      const lastDate = series[0].points[series[0].points.length - 1]?.date || '';
      svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
      svg.innerHTML = `<rect width="${width}" height="${height}" fill="#ffffff"/>${grid}<line x1="${pad.left}" y1="${height - pad.bottom}" x2="${width - pad.right}" y2="${height - pad.bottom}" stroke="#cbd5e1"/><line x1="${pad.left}" y1="${pad.top}" x2="${pad.left}" y2="${height - pad.bottom}" stroke="#cbd5e1"/>${paths}<text x="${pad.left}" y="${height - 26}" fill="#64748b" font-size="12">${firstDate}</text><text x="${width - pad.right}" y="${height - 26}" text-anchor="end" fill="#64748b" font-size="12">${lastDate}</text>${legend}`;
    }
    drawEquityChart();
    window.addEventListener('resize', drawEquityChart);
    fetch('/status').then(r => r.json()).then(data => { document.querySelectorAll('[data-count="history"]').forEach(n => n.textContent=data.history_count); document.querySelectorAll('[data-count="cache"]').forEach(n => n.textContent=data.cache_count); }).catch(() => {});
  </script>
</body>
</html>
"""

LOGIN_PAGE_TEMPLATE = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>登录 - AI 量化智能体</title>
  <style>
    :root { --bg:#eef1f4; --panel:#ffffff; --ink:#172033; --muted:#667085; --brand:#126e82; --line:#d9e0e7; --shadow:0 1px 2px rgba(16,24,40,.06); }
    * { box-sizing:border-box; }
    body { margin:0; min-height:100vh; display:grid; place-items:center; padding:20px; font-family:"Microsoft YaHei","PingFang SC",Arial,sans-serif; color:var(--ink); background:var(--bg); }
    .card { width:min(420px,calc(100vw - 32px)); padding:24px; border-radius:8px; background:var(--panel); border:1px solid var(--line); box-shadow:var(--shadow); }
    .eyebrow { display:inline-block; margin-bottom:12px; padding:4px 8px; border-radius:4px; background:#e6f4f1; color:var(--brand); font-size:11px; font-weight:800; letter-spacing:.04em; }
    h1 { margin:0 0 20px; font-size:26px; }
    .field { display:grid; gap:6px; margin-bottom:14px; }
    label { font-size:12px; font-weight:700; color:#344054; }
    input { width:100%; border:1px solid #cfd7df; border-radius:6px; padding:10px; font:inherit; background:#fff; }
    button { width:100%; border:0; border-radius:6px; padding:11px; color:#fff; font-weight:700; font-size:15px; background:var(--brand); cursor:pointer; }
    .muted { color:var(--muted); line-height:1.6; font-size:14px; margin-top:16px; text-align:center; }
    .muted a { color:var(--brand); font-weight:700; text-decoration:none; }
    .notice { padding:10px 12px; border-radius:6px; background:#fff7ed; color:#9a3412; border:1px solid #fed7aa; margin-bottom:14px; font-size:14px; }
    .notice.error { background:#fef2f2; color:#b91c1c; border-color:#fecaca; }
  </style>
</head>
<body>
  <div class="card">
    <div class="eyebrow">ACCOUNT</div>
    <h1>欢迎回来</h1>
    {% if error %}<div class="notice error">{{ error }}</div>{% endif %}
    {% if note %}<div class="notice">{{ note }}</div>{% endif %}
    <form method="post">
      <div class="field"><label for="username">用户名</label><input id="username" name="username" placeholder="请输入用户名" required></div>
      <div class="field"><label for="password">密码</label><input id="password" name="password" type="password" placeholder="请输入密码" required></div>
      <button type="submit">登录</button>
    </form>
    <div class="muted">还没有账号？<a href="{{ url_for('register') }}">立即注册</a></div>
  </div>
</body>
</html>
"""

REGISTER_PAGE_TEMPLATE = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>注册 - AI 量化智能体</title>
  <style>
    :root { --bg:#eef1f4; --panel:#ffffff; --ink:#172033; --muted:#667085; --brand:#126e82; --accent:#7a5b12; --line:#d9e0e7; --shadow:0 1px 2px rgba(16,24,40,.06); }
    * { box-sizing:border-box; }
    body { margin:0; min-height:100vh; display:grid; place-items:center; padding:20px; font-family:"Microsoft YaHei","PingFang SC",Arial,sans-serif; color:var(--ink); background:var(--bg); }
    .card { width:min(420px,calc(100vw - 32px)); padding:24px; border-radius:8px; background:var(--panel); border:1px solid var(--line); box-shadow:var(--shadow); }
    .eyebrow { display:inline-block; margin-bottom:12px; padding:4px 8px; border-radius:4px; background:#e6f4f1; color:var(--brand); font-size:11px; font-weight:800; letter-spacing:.04em; }
    h1 { margin:0 0 20px; font-size:26px; }
    .field { display:grid; gap:6px; margin-bottom:14px; }
    label { font-size:12px; font-weight:700; color:#344054; }
    input { width:100%; border:1px solid #cfd7df; border-radius:6px; padding:10px; font:inherit; background:#fff; }
    button { width:100%; border:0; border-radius:6px; padding:11px; color:#fff; font-weight:700; font-size:15px; background:var(--accent); cursor:pointer; }
    .muted { color:var(--muted); line-height:1.6; font-size:14px; margin-top:16px; text-align:center; }
    .muted a { color:var(--brand); font-weight:700; text-decoration:none; }
    .notice { padding:10px 12px; border-radius:6px; background:#fff7ed; color:#9a3412; border:1px solid #fed7aa; margin-bottom:14px; font-size:14px; }
    .notice.error { background:#fef2f2; color:#b91c1c; border-color:#fecaca; }
  </style>
</head>
<body>
  <div class="card">
    <div class="eyebrow">ACCOUNT</div>
    <h1>创建账号</h1>
    {% if error %}<div class="notice error">{{ error }}</div>{% endif %}
    {% if note %}<div class="notice">{{ note }}</div>{% endif %}
    <form method="post">
      <div class="field"><label for="username">用户名</label><input id="username" name="username" placeholder="请输入用户名" required></div>
      <div class="field"><label for="password">密码</label><input id="password" name="password" type="password" placeholder="请设置密码（至少 6 位）" required></div>
      <div class="field"><label for="password2">确认密码</label><input id="password2" name="password2" type="password" placeholder="再次输入密码" required></div>
      <button type="submit">注册</button>
    </form>
    <div class="muted">已有账号？<a href="{{ url_for('login') }}">去登录</a></div>
  </div>
</body>
</html>
"""

STRATEGY_PAGE_TEMPLATE = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>褰撳墠绛栫暐 - AI 閲忓寲鏅鸿兘浣</title>
  <style>
    :root {
      --bg: #f3eadc;
      --panel: rgba(255, 251, 244, .9);
      --ink: #14213d;
      --muted: #5f6b7a;
      --brand: #0e7490;
      --accent: #b45309;
      --line: rgba(170, 147, 112, .28);
      --shadow: 0 22px 55px rgba(19, 35, 62, .10);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at 10% 0%, rgba(14, 116, 144, .13), transparent 28%),
        radial-gradient(circle at 100% 8%, rgba(180, 83, 9, .12), transparent 30%),
        linear-gradient(180deg, #fbf4e9 0%, var(--bg) 100%);
      min-height: 100vh;
    }
    .shell {
      max-width: 1100px;
      margin: 0 auto;
      padding: 26px 22px 44px;
    }
    .topbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 14px;
      margin-bottom: 20px;
    }
    .back {
      width: auto;
      display: inline-flex;
      align-items: center;
      padding: 10px 14px;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,.74);
      color: var(--brand);
      text-decoration: none;
      font-weight: 700;
      font-size: 13px;
    }
    .hero, .section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 26px;
      box-shadow: var(--shadow);
      padding: 28px;
      margin-bottom: 18px;
    }
    .eyebrow {
      display: inline-block;
      margin-bottom: 14px;
      padding: 8px 13px;
      border-radius: 999px;
      background: rgba(14, 116, 144, .10);
      color: var(--brand);
      font-size: 12px;
      font-weight: 800;
      letter-spacing: .06em;
    }
    h1 { margin: 0 0 12px; font-size: clamp(28px, 4vw, 44px); }
    h2 { margin: 0 0 14px; font-size: 22px; }
    h3 { margin: 18px 0 8px; font-size: 17px; color: var(--brand); }
    p, li { margin: 0; color: var(--muted); line-height: 1.85; font-size: 14px; }
    ul { margin: 8px 0; padding-left: 20px; }
    li { margin-bottom: 6px; }
    .grid-2 {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 18px;
    }
    .metric-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 14px;
    }
    .metric {
      padding: 18px;
      border-radius: 18px;
      background: linear-gradient(180deg, rgba(255,255,255,.92), rgba(252,246,236,.85));
      border: 1px solid var(--line);
    }
    .metric-label { color: var(--muted); font-size: 12px; font-weight: 700; margin-bottom: 6px; }
    .metric-value { font-size: 22px; font-weight: 900; }
    .tag {
      display: inline-flex;
      padding: 5px 10px;
      border-radius: 999px;
      background: rgba(14,116,144,.09);
      color: var(--brand);
      font-size: 12px;
      font-weight: 700;
      margin-right: 6px;
      margin-bottom: 6px;
    }
    .tag.accent {
      background: rgba(180,83,9,.09);
      color: var(--accent);
    }
    .code {
      background: #f6f1e8;
      border: 1px dashed var(--line);
      border-radius: 12px;
      padding: 14px 16px;
      font-family: "Consolas", "Monaco", monospace;
      font-size: 13px;
      color: #374151;
      line-height: 1.7;
      white-space: pre-wrap;
      margin-top: 10px;
    }
    .flow {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
      margin: 14px 0;
    }
    .flow-item {
      padding: 10px 14px;
      border-radius: 14px;
      background: linear-gradient(135deg, var(--brand-soft, #dff6fb), rgba(255,255,255,.8));
      border: 1px solid rgba(14,116,144,.18);
      font-size: 13px;
      font-weight: 700;
      color: var(--brand);
    }
    .flow-arrow {
      color: var(--muted);
      font-size: 18px;
    }
    @media (max-width: 760px) {
      .grid-2, .metric-grid { grid-template-columns: 1fr; }
      .hero, .section { padding: 22px; }
    }
  </style>
</head>
<body>
  <main class="shell">
    <div class="topbar">
      <a class="back" href="{{ url_for('index') }}">鈫?杩斿洖鍒嗘瀽棣栭〉</a>
      <span class="back" style="color:var(--muted);">AI 閲忓寲鏅鸿兘浣撶瓥鐣ヨ鏄庝功</span>
    </div>

    <section class="hero">
      <div class="eyebrow">STRATEGY DOCUMENT</div>
      <h1>褰撳墠绛栫暐浣撶郴</h1>
      <p>鏈〉瀹屾暣灞曠ず绯荤粺浣跨敤鐨勬妧鏈寚鏍囥€佷俊鍙疯鍒欍€佸洖娴嬪弬鏁般€侀鎺ч厤缃拰 AI 铻嶅悎鍐崇瓥閫昏緫銆傛墍鏈夊弬鏁板潎鏉ヨ嚜 <code>config.yaml</code> 涓庝唬鐮佷腑鐨勯粯璁ら厤缃€</p>
    </section>

    <section class="section">
      <h2>馃М 鎶€鏈寚鏍囦綋绯</h2>
      <p>绯荤粺鍦ㄥ垎鏋愭椂榛樿涓€閿绠椾互涓?6 澶х被鎸囨爣锛</p>
      <div class="metric-grid" style="margin-top:14px;">
        <div class="metric">
          <div class="metric-label">绉诲姩骞冲潎绾</div>
          <div class="metric-value">MA5/10/20/30/60</div>
        </div>
        <div class="metric">
          <div class="metric-label">MACD</div>
          <div class="metric-value">12,26,9</div>
        </div>
        <div class="metric">
          <div class="metric-label">RSI</div>
          <div class="metric-value">鍛ㄦ湡 {{ config.rsi_period }}</div>
        </div>
        <div class="metric">
          <div class="metric-label">甯冩灄甯</div>
          <div class="metric-value">20, 2.0蟽</div>
        </div>
        <div class="metric">
          <div class="metric-label">KDJ</div>
          <div class="metric-value">9,3,3</div>
        </div>
        <div class="metric">
          <div class="metric-label">ATR</div>
          <div class="metric-value">鍛ㄦ湡 14</div>
        </div>
      </div>
    </section>

    <section class="section">
      <h2>馃摗 淇″彿鐢熸垚瑙勫垯</h2>
      <div class="grid-2">
        <div>
          <h3>鍧囩嚎浜ゅ弶绛栫暐</h3>
          <ul>
            <li>蹇嚎 <strong>MA{{ config.fast_window }}</strong> 涓婄┛鎱㈢嚎 <strong>MA{{ config.slow_window }}</strong> 鈫?<span style="color:#047857;font-weight:700;">閲戝弶涔板叆</span></li>
            <li>蹇嚎涓嬬┛鎱㈢嚎 鈫?<span style="color:#b91c1c;font-weight:700;">姝诲弶鍗栧嚭</span></li>
          </ul>
        </div>
        <div>
          <h3>RSI 鍙嶈浆绛栫暐</h3>
          <ul>
            <li>RSI 浠庤秴鍗栧尯(&lt;{{ config.rsi_oversold }})鍥炲崌 鈫?<span style="color:#047857;font-weight:700;">涔板叆淇″彿</span></li>
            <li>RSI 浠庤秴涔板尯(&gt;{{ config.rsi_overbought }})鍥炶惤 鈫?<span style="color:#b91c1c;font-weight:700;">鍗栧嚭淇″彿</span></li>
          </ul>
        </div>
        <div>
          <h3>MACD 閲戝弶绛栫暐</h3>
          <ul>
            <li>MACD 绾夸笂绌?Signal 绾?鈫?<span style="color:#047857;font-weight:700;">涔板叆</span></li>
            <li>MACD 绾夸笅绌?Signal 绾?鈫?<span style="color:#b91c1c;font-weight:700;">鍗栧嚭</span></li>
          </ul>
        </div>
        <div>
          <h3>澶氱瓥鐣ュ悎鎴愶紙鎶曠エ鏈哄埗锛</h3>
          <ul>
            <li>3 涓瓙绛栫暐鍚勮緭鍑?-1/0/+1</li>
            <li>鎬诲垎 鈮?+2 鈫?<strong>缁煎悎涔板叆</strong></li>
            <li>鎬诲垎 鈮?-2 鈫?<strong>缁煎悎鍗栧嚭</strong></li>
            <li>鍚﹀垯 鈫?<strong>瑙傛湜</strong></li>
          </ul>
        </div>
      </div>
    </section>

    <section class="section">
      <h2>鈿欙笍 绛栫暐璇勫垎缁嗗垯锛圦uantAgent 鍐呯疆锛</h2>
      <p>绯荤粺瀵规渶鏂拌鎯呮暟鎹繘琛岄€愰」璇勫垎锛屾渶缁堝緱鍒扮▼搴忎氦鏄撲俊鍙凤細</p>
      <div class="code">鍧囩嚎:   MA{{ config.fast_window }} &gt; MA{{ config.slow_window }}  鈫?+1锛屽惁鍒?-1
MACD:   MACD &gt; Signal  鈫?+1锛屽惁鍒?-1
RSI:    &lt;{{ config.rsi_oversold }} 鈫?+2  |  &gt;{{ config.rsi_overbought }} 鈫?-2  |  &lt;45 鈫?+1  |  &gt;55 鈫?-1
甯冩灄甯? close &lt; 涓嬭建 鈫?+1  |  close &gt; 涓婅建 鈫?-1

寰楀垎 鈮?+2  鈫?鍋氬淇″彿(1)
寰楀垎 鈮?-2  鈫?绌轰粨淇″彿(0)  [A鑲′笉鏂逛究鍋氱┖]
鍚﹀垯       鈫?瑙傛湜(0)</div>
    </section>

    <section class="section">
      <h2>馃 AI 铻嶅悎鍐崇瓥寮曟搸</h2>
      <p>绋嬪簭淇″彿涓?AI 鍒嗘瀽鎶ュ憡杩涜铻嶅悎锛岀敓鎴愭渶缁堜氦鏄撳喅绛栵細</p>
      <div class="flow">
        <div class="flow-item">绋嬪簭淇″彿</div>
        <span class="flow-arrow">+</span>
        <div class="flow-item">AI 淇″彿</div>
        <span class="flow-arrow">鈫</span>
        <div class="flow-item">椋庢帶妫€鏌</div>
        <span class="flow-arrow">鈫</span>
        <div class="flow-item">鏈€缁堝喅绛</div>
      </div>
      <div class="code">score = 绋嬪簭淇″彿 + AI淇″彿  (鑼冨洿: -2 ~ +2)

score 鈮?+2   鈫?寮虹儓涔板叆  (楂樼疆淇″害)
score = +1   鈫?璋ㄦ厧涔板叆  (寤鸿杞讳粨)
score =  0   鈫?鍐茬獊瑙傛湜  (缁存寔鐜扮姸)
score = -1   鈫?璋ㄦ厧鍗栧嚭  (鎸佷粨鑰呭噺浠?
score 鈮?-2   鈫?寮虹儓鍗栧嚭  (楂樼疆淇″害)

椋庢帶鏆傚仠鏃?鈫?寮哄埗瑙傛湜锛屾棤瑙嗕俊鍙</div>
    </section>

    <section class="section">
      <h2>馃搳 鍥炴祴閰嶇疆</h2>
      <div class="metric-grid">
        <div class="metric">
          <div class="metric-label">鍒濆璧勯噾</div>
          <div class="metric-value">{{ "{:,.0f}".format(config.initial_cash) }} 鍏</div>
        </div>
        <div class="metric">
          <div class="metric-label">鎵嬬画璐圭巼</div>
          <div class="metric-value">{{ "{:.2%}".format(config.commission) }}</div>
        </div>
        <div class="metric">
          <div class="metric-label">婊戠偣</div>
          <div class="metric-value">{{ "{:.1%}".format(config.slippage) }}</div>
        </div>
      </div>
      <h3>鍩洪噾鐢宠祹璐圭巼</h3>
      <p>鍦哄鍩洪噾鍥炴祴鏃惰嚜鍔ㄨ鍏ョ敵璐垂涓庤祹鍥炶垂闃舵锛</p>
      <div style="margin-top:10px;">
        <span class="tag">鐢宠喘璐?{{ "{:.2%}".format(config.subscribe_fee) }}</span>
        <span class="tag accent">&lt;7澶?璧庡洖 {{ "{:.2%}".format(config.redeem_7) }}</span>
        <span class="tag accent">7-30澶?{{ "{:.2%}".format(config.redeem_30) }}</span>
        <span class="tag accent">30-365澶?{{ "{:.2%}".format(config.redeem_365) }}</span>
        <span class="tag accent">&gt;365澶?鍏嶈垂</span>
      </div>
    </section>

    <section class="section">
      <h2>馃洝锔?椋庢帶瑙勫垯</h2>
      <div class="grid-2">
        <div>
          <h3>浠撲綅涓庝氦鏄撻檺鍒</h3>
          <ul>
            <li>鍗曟爣浠撲綅涓婇檺锛?strong>{{ "{:.0%}".format(risk.max_position_pct) }}</strong></li>
            <li>鏈€澶ф寔浠撴暟锛?strong>{{ risk.max_total_positions }} 鍙</strong></li>
            <li>鏈€浣庣幇閲戠暀瀛橈細<strong>{{ "{:.0%}".format(risk.min_cash_ratio) }}</strong></li>
            <li>鍗曟棩涓嬪崟涓婇檺锛?strong>{{ risk.max_orders_per_day }} 娆</strong></li>
            <li>鍚屾爣鐨勫喎鍗达細<strong>{{ risk.cooldown_minutes }} 鍒嗛挓</strong></li>
          </ul>
        </div>
        <div>
          <h3>姝㈡崯姝㈢泩涓庡洖鎾</h3>
          <ul>
            <li>涓偂姝㈡崯绾匡細<strong>{{ "{:.0%}".format(risk.stop_loss_pct) }}</strong></li>
            <li>涓偂姝㈢泩绾匡細<strong>{{ "{:.0%}".format(risk.take_profit_pct) }}</strong></li>
            <li>绉诲姩姝㈡崯鍥炴挙锛?strong>{{ "{:.0%}".format(risk.trailing_stop_pct) }}</strong></li>
            <li>鍗曟棩浜忔崯涓婇檺锛?strong>{{ "{:.0%}".format(risk.max_daily_loss_pct) }}</strong></li>
            <li>缁勫悎鏈€澶у洖鎾わ細<strong>{{ "{:.0%}".format(risk.max_drawdown_pct) }}</strong> 鈫?鍔ㄤ綔锛?strong>{{ risk.drawdown_action }}</strong></li>
          </ul>
        </div>
      </div>
    </section>

    <section class="section">
      <h2>馃敩 钂欑壒鍗℃礇妯℃嫙</h2>
      <p>鍥炴祴寮曟搸鍐呯疆 Bootstrap 钂欑壒鍗℃礇妯℃嫙锛岀敤浜庤瘎浼扮瓥鐣ラ闄╁垎甯冿細</p>
      <ul>
        <li>妯℃嫙娆℃暟锛?strong>10,000 娆</strong></li>
        <li>妯℃嫙鍛ㄦ湡锛?strong>252 涓氦鏄撴棩</strong>锛堢害涓€骞达級</li>
        <li>杈撳嚭鎸囨爣锛氳儨鐜囥€佸钩鍧囨敹鐩娿€佷腑浣嶆暟鏀剁泭銆佹渶濂?鏈€宸?5% 鏀剁泭銆佹渶澶у洖鎾ゅ垎甯冦€佸洖鎾よ秴 20%/30% 姒傜巼</li>
      </ul>
    </section>
  </main>
</body>
</html>
"""

HISTORY_PAGE_TEMPLATE = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>缁忔祹鍘嗗彶鏃堕棿绾</title>
  <style>
    :root {
      --bg: #f3eadc;
      --panel: rgba(255, 251, 244, .88);
      --ink: #14213d;
      --muted: #5f6b7a;
      --brand: #0e7490;
      --accent: #b45309;
      --line: rgba(170, 147, 112, .28);
      --shadow: 0 22px 55px rgba(19, 35, 62, .10);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at 10% 0%, rgba(14, 116, 144, .13), transparent 28%),
        radial-gradient(circle at 100% 8%, rgba(180, 83, 9, .12), transparent 30%),
        linear-gradient(180deg, #fbf4e9 0%, var(--bg) 100%);
      min-height: 100vh;
    }
    .shell {
      max-width: 1180px;
      margin: 0 auto;
      padding: 26px 22px 44px;
    }
    .topbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 14px;
      margin-bottom: 20px;
    }
    .back {
      width: auto;
      display: inline-flex;
      align-items: center;
      padding: 10px 14px;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,.74);
      color: var(--brand);
      text-decoration: none;
      font-weight: 700;
      font-size: 13px;
    }
    .hero, .quote, .timeline, .pattern-grid, .metric-grid, .compare-note {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 26px;
      box-shadow: var(--shadow);
    }
    .hero {
      padding: 34px;
      margin-bottom: 18px;
    }
    .eyebrow {
      display: inline-block;
      margin-bottom: 14px;
      padding: 8px 13px;
      border-radius: 999px;
      background: rgba(14, 116, 144, .10);
      color: var(--brand);
      font-size: 12px;
      font-weight: 800;
      letter-spacing: .06em;
    }
    h1 {
      margin: 0 0 12px;
      font-size: clamp(34px, 5vw, 58px);
      line-height: 1.05;
    }
    h2 {
      margin: 0 0 14px;
      font-size: 24px;
    }
    p {
      margin: 0;
      color: var(--muted);
      line-height: 1.85;
    }
    .quote {
      padding: 24px 28px;
      margin-bottom: 18px;
      border-left: 6px solid var(--accent);
    }
    .quote strong {
      display: block;
      font-size: clamp(22px, 3vw, 34px);
      line-height: 1.35;
      margin-bottom: 10px;
    }
    .section-title {
      display: flex;
      justify-content: space-between;
      align-items: end;
      gap: 16px;
      margin: 28px 0 12px;
    }
    .timeline {
      padding: 8px 24px;
    }
    .event {
      display: grid;
      grid-template-columns: 120px 1fr;
      gap: 18px;
      padding: 20px 0;
      border-bottom: 1px solid var(--line);
    }
    .event:last-child { border-bottom: 0; }
    .year {
      color: var(--accent);
      font-weight: 900;
      font-size: 20px;
    }
    .event h3 {
      margin: 0 0 8px;
      font-size: 18px;
    }
    .tags {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 12px;
    }
    .tag {
      padding: 6px 9px;
      border-radius: 999px;
      background: rgba(14,116,144,.09);
      color: var(--brand);
      font-size: 12px;
      font-weight: 700;
    }
    .metric-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 0;
      overflow: hidden;
    }
    .metric {
      padding: 22px;
      border-right: 1px solid var(--line);
      background: linear-gradient(180deg, rgba(255,255,255,.52), rgba(255,251,244,.18));
    }
    .metric:last-child { border-right: 0; }
    .metric-label {
      color: var(--muted);
      font-size: 13px;
      font-weight: 700;
      margin-bottom: 8px;
    }
    .metric-value {
      font-size: clamp(24px, 3vw, 34px);
      font-weight: 900;
      line-height: 1.1;
      margin-bottom: 10px;
      color: var(--ink);
    }
    .metric-formula {
      display: inline-flex;
      padding: 6px 9px;
      border-radius: 999px;
      background: rgba(180, 83, 9, .09);
      color: var(--accent);
      font-size: 12px;
      font-weight: 800;
      margin-bottom: 12px;
    }
    .compare-note {
      padding: 18px 22px;
      margin-top: 12px;
      border-radius: 20px;
    }
    .pattern-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 0;
      overflow: hidden;
    }
    .pattern {
      padding: 22px;
      border-right: 1px solid var(--line);
    }
    .pattern:last-child { border-right: 0; }
    .pattern h3 {
      margin: 0 0 8px;
      font-size: 18px;
    }
    @media (max-width: 760px) {
      .event { grid-template-columns: 1fr; gap: 8px; }
      .metric-grid { grid-template-columns: 1fr; }
      .metric { border-right: 0; border-bottom: 1px solid var(--line); }
      .metric:last-child { border-bottom: 0; }
      .pattern-grid { grid-template-columns: 1fr; }
      .pattern { border-right: 0; border-bottom: 1px solid var(--line); }
      .pattern:last-child { border-bottom: 0; }
      .hero { padding: 26px; }
    }
  </style>
</head>
<body>
  <main class="shell">
    <div class="topbar">
      <a class="back" href="{{ url_for('index') }}">杩斿洖鍒嗘瀽棣栭〉</a>
      <a class="back" href="{{ url_for('index') }}#history">鍒嗘瀽璁板綍</a>
    </div>

    <section class="hero">
      <div class="eyebrow">ECONOMIC HISTORY</div>
      <h1>缁忔祹鍘嗗彶涓庨噸澶т簨浠</h1>
      <p>杩欓〉鐢ㄦ椂闂寸嚎鎶婇噾铻嶅競鍦哄弽澶嶅嚭鐜扮殑涓婚涓茶捣鏉ワ細淇＄敤鎵╁紶銆佽祫浜ф场娌€佹斂绛栬浆鍚戙€侀€氳儉鍐插嚮銆佹妧鏈潻鍛藉拰鍏ㄧ悆鍖栭噸缁勩€傚畠涓嶆槸棰勬祴琛紝浣嗚兘甯綘鍦ㄥ垎鏋愯鎯呮椂澶氫竴灞傚巻鍙插弬鐓с€</p>
    </section>

    <section class="quote">
      <strong>鈥滃巻鍙蹭笉浼氶噸澶嶈嚜宸憋紝浣嗗畠甯稿父鎶奸煹銆傗€</strong>
      <p>杩欏彞璇濆父琚綊浜庨┈鍏嬄峰悙娓┿€傜敤鍦ㄥ競鍦洪噷寰堝悎閫傦細姣忎竴杞懆鏈熺殑缁嗚妭涓嶅悓锛屼絾浜烘€с€佹潬鏉嗐€佹祦鍔ㄦ€у拰鍙欎簨缁忓父浠ョ浉浼肩殑鑺傚鍑虹幇銆</p>
    </section>

    <div class="section-title">
      <h2>璺ㄨ祫浜ф敹鐩婄巼涓庡€嶆暟</h2>
      <p>鎶婅偂绁ㄣ€佸€哄埜銆佹埧鍦颁骇鍜屾敹璐斁鍒板悓涓€寮犱及鍊煎湴鍥句笂</p>
    </div>
    <section class="metric-grid">
      {% for metric in valuation_metrics %}
      <article class="metric">
        <div class="metric-label">{{ metric.label }}</div>
        <div class="metric-value">{{ metric.value }}</div>
        <div class="metric-formula">{{ metric.formula }}</div>
        <p>{{ metric.summary }}</p>
      </article>
      {% endfor %}
    </section>
    <section class="compare-note">
      <p>鏍稿績姣旇緝鏂瑰紡锛氭敹鐩婄巼瓒婇珮锛屼唬琛ㄥ悓鏍风幇閲戞祦瀵瑰簲鐨勪环鏍艰秺浣庯紱鍊嶆暟瓒婇珮锛屼唬琛ㄥ悓鏍风幇閲戞祦瀵瑰簲鐨勪环鏍艰秺楂樸€傜矖鐣ユ崲绠楁椂锛岀幇閲戞祦鍊嶆暟鍙互鐪嬩綔鏀剁泭鐜囩殑鍊掓暟锛屼緥濡?10 鍊嶇幇閲戞祦绾︾瓑浜?10% 鐜伴噾娴佹敹鐩婄巼锛?0 鍊嶇害绛変簬 5%銆</p>
    </section>

    <div class="section-title">
      <h2>閲嶅ぇ浜嬩欢鏃堕棿绾</h2>
      <p>浠庢棭鏈熸场娌埌鐜颁唬璐у竵鏀跨瓥鍛ㄦ湡</p>
    </div>
    <section class="timeline">
      {% for event in events %}
      <article class="event">
        <div class="year">{{ event.year }}</div>
        <div>
          <h3>{{ event.title }}</h3>
          <p>{{ event.summary }}</p>
          <div class="tags">
            {% for tag in event.tags %}
              <span class="tag">{{ tag }}</span>
            {% endfor %}
          </div>
        </div>
      </article>
      {% endfor %}
    </section>

    <div class="section-title">
      <h2>鍙嶅鍑虹幇鐨勪富绾</h2>
      <p>璇诲巻鍙叉椂鏈€鍊煎緱鐩綇鐨勫嚑涓彉閲</p>
    </div>
    <section class="pattern-grid">
      <div class="pattern">
        <h3>娴佸姩鎬</h3>
        <p>瀹芥澗璧勯噾甯告帹鍔ㄤ及鍊兼墿寮狅紝绱х缉璧勯噾鍒欎細鏆撮湶鏉犳潌鍜岀幇閲戞祦闂銆</p>
      </div>
      <div class="pattern">
        <h3>鍙欎簨</h3>
        <p>閾佽矾銆佺數鍔涖€佷簰鑱旂綉銆丄I 绛夋妧鏈氮娼兘浼氬厛鏀瑰彉鎯宠薄鍔涳紝鍐嶆帴鍙楃泩鍒╅獙璇併€</p>
      </div>
      <div class="pattern">
        <h3>鏀跨瓥</h3>
        <p>姹囩巼銆佸埄鐜囥€佽储鏀夸笌鐩戠鍙樺寲锛屽線寰€鍐冲畾鍛ㄦ湡鐨勯€熷害銆佸箙搴﹀拰淇璺緞銆</p>
      </div>
    </section>
  </main>
</body>
</html>
"""

BACKTEST_COMPARE_TEMPLATE = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>策略对比</title>
  <style>
    :root { --bg:#eef1f4; --panel:#ffffff; --ink:#172033; --muted:#667085; --brand:#126e82; --line:#d9e0e7; --shadow:0 1px 2px rgba(16,24,40,.06); }
    body { margin: 0; font-family: "Microsoft YaHei", "PingFang SC", sans-serif; background: var(--bg); color: var(--ink); font-size:14px; }
    .shell { max-width: 1180px; margin: 0 auto; padding: 16px 20px 40px; }
    .panel { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 16px; margin-bottom: 12px; box-shadow:var(--shadow); }
    h1 { margin:0 0 8px; font-size:28px; }
    .row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; align-items:end; }
    label { display: grid; gap: 6px; font-weight: 700; font-size: 12px; color:#344054; }
    input, select, button { padding: 9px 10px; border-radius: 6px; border: 1px solid #cfd7df; font: inherit; background:#fff; }
    button, .back { background: var(--brand); color: white; border: 0; text-decoration: none; display: inline-flex; justify-content: center; border-radius:6px; font-weight:800; }
    .back { padding:7px 12px; }
    table { width: 100%; border-collapse: collapse; min-width: 760px; }
    th, td { text-align: left; padding: 9px 8px; border-bottom: 1px solid var(--line); font-family:Consolas,"Microsoft YaHei",monospace; }
    th { background:#f3f6f8; color:#475467; font-size:12px; font-family:"Microsoft YaHei","PingFang SC",sans-serif; }
    tr:last-child td { border-bottom:0; }
    .table-wrap { overflow-x: auto; }
    .muted { color: var(--muted); line-height: 1.6; }
    @media (max-width: 760px) { .row { grid-template-columns: 1fr; } .shell { padding: 12px; } }
  </style>
</head>
<body>
  <div class="shell">
    <p><a class="back" href="{{ url_for('index') }}">返回控制台</a></p>
    <div class="panel">
      <h1>历史表现复盘对比</h1>
      <p class="muted">同一标的、同一周期下比较不同观察规则的历史表现，用于复核风险和稳定性，不作为买卖指令。</p>
      <form method="get">
        <div class="row">
          <label>代码 <input name="symbol" value="{{ symbol }}"></label>
          <label>市场
            <select name="market">
              {% for item in ['fund', 'a_stock', 'us_stock', 'crypto'] %}
              <option value="{{ item }}" {% if market == item %}selected{% endif %}>{{ item }}</option>
              {% endfor %}
            </select>
          </label>
          <label>周期
            <select name="period">
              {% for item in ['1mo', '3mo', '6mo', '1y', '2y', '3y', '5y', '10y', '20y', '50y', 'max'] %}
              <option value="{{ item }}" {% if period == item %}selected{% endif %}>{{ item }}</option>
              {% endfor %}
            </select>
          </label>
          <label>&nbsp;<button type="submit">运行对比</button></label>
        </div>
      </form>
    </div>
    {% if error %}
    <div class="panel"><strong>{{ error }}</strong></div>
    {% endif %}
    {% if rows %}
    <div class="panel table-wrap">
      <table>
        <thead>
          <tr>
            <th>策略</th><th>总收益</th><th>CAGR</th><th>最大回撤</th><th>夏普</th><th>交易次数</th><th>胜率</th><th>期末资产</th>
          </tr>
        </thead>
        <tbody>
          {% for row in rows %}
          <tr>
            <td>{{ row.name }}</td>
            <td>{{ "%.2f%%"|format(row.total_return * 100) }}</td>
            <td>{{ "%.2f%%"|format(row.cagr * 100) }}</td>
            <td>{{ "%.2f%%"|format(row.max_drawdown * 100) }}</td>
            <td>{{ "%.2f"|format(row.sharpe_ratio) }}</td>
            <td>{{ row.trade_count }}</td>
            <td>{{ "%.1f%%"|format(row.win_rate * 100) }}</td>
            <td>{{ "%.2f"|format(row.final_value) }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
    {% endif %}
  </div>
</body>
</html>
"""

CLEAN_STRATEGY_PAGE_TEMPLATE = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>当前策略 - AI 量化智能体</title>
  <style>
    :root { --bg:#eef1f4; --panel:#ffffff; --panel-2:#f7f9fb; --ink:#172033; --muted:#667085; --brand:#126e82; --accent:#7a5b12; --line:#d9e0e7; --shadow:0 1px 2px rgba(16,24,40,.06); }
    * { box-sizing:border-box; }
    body { margin:0; font-family:"Microsoft YaHei","PingFang SC",Arial,sans-serif; color:var(--ink); background:var(--bg); min-height:100vh; font-size:14px; }
    .top { max-width:1400px; margin:0 auto; padding:12px 20px; display:flex; justify-content:space-between; gap:10px; border-bottom:1px solid var(--line); background:#f9fafb; }
    .back { display:inline-flex; padding:7px 12px; border-radius:6px; background:#fff; color:var(--brand); border:1px solid var(--line); text-decoration:none; font-weight:800; }
    .shell { max-width:1400px; margin:0 auto; padding:16px 20px 40px; }
    .panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; box-shadow:var(--shadow); padding:20px; margin-bottom:12px; }
    .eyebrow { display:inline-flex; padding:4px 8px; border-radius:4px; background:#e6f4f1; color:var(--brand); font-size:11px; font-weight:800; letter-spacing:.04em; text-transform:uppercase; }
    h1 { margin:10px 0 8px; font-size:30px; line-height:1.16; }
    h2 { margin:0 0 12px; font-size:18px; padding-bottom:10px; border-bottom:1px solid var(--line); }
    h3 { margin:0 0 8px; font-size:15px; color:var(--brand); }
    p,li,.muted { color:var(--muted); line-height:1.6; }
    .metric-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:0; margin-top:14px; border:1px solid var(--line); border-radius:8px; overflow:hidden; }
    .metric { padding:14px; border-right:1px solid var(--line); border-bottom:1px solid var(--line); background:#fff; }
    .metric:nth-child(3n) { border-right:0; }
    .metric:nth-last-child(-n+3) { border-bottom:0; }
    .metric-label { color:var(--muted); font-weight:800; margin-bottom:6px; font-size:12px; }
    .metric-value { font-size:22px; font-weight:900; color:#0f172a; font-family:Consolas,"SFMono-Regular",monospace; }
    .rule-grid { display:grid; grid-template-columns:repeat(2,1fr); gap:12px; }
    .rule-grid > div { padding:14px; border:1px solid var(--line); border-radius:8px; background:var(--panel-2); }
    .code { white-space:pre-wrap; background:#101828; color:#eef4ff; border-radius:8px; padding:14px; line-height:1.65; overflow:auto; font-family:Consolas,"Microsoft YaHei",monospace; font-size:13px; }
    .flow { display:flex; flex-wrap:wrap; gap:10px; align-items:center; }
    .flow-item { padding:8px 10px; border-radius:6px; background:#e6f4f1; color:var(--brand); font-weight:800; border:1px solid #c8e7e1; }
    .warn { color:#b91c1c; font-weight:800; }
    .ok { color:#047857; font-weight:800; }
    @media (max-width:900px) { .metric-grid,.rule-grid { grid-template-columns:1fr; } .metric,.metric:nth-child(3n),.metric:nth-last-child(-n+3) { border-right:0; border-bottom:1px solid var(--line); } h1 { font-size:26px; } .shell,.top { padding-left:12px; padding-right:12px; } }
  </style>
</head>
<body>
  <div class="top">
    <a class="back" href="{{ url_for('index') }}">返回控制台</a>
    <a class="back" href="{{ url_for('backtest_compare') }}">打开策略对比</a>
  </div>
  <main class="shell">
    <section class="panel">
      <div class="eyebrow">STRATEGY DOCUMENT</div>
      <h1>当前策略配置</h1>
      <p>本页展示系统用于分析和回测的指标、信号规则、回测参数和风控默认值。参数来自 <code>config.yaml</code> 与代码中的默认配置。</p>
    </section>

    <section class="panel">
      <h2>技术指标体系</h2>
      <p>系统会在行情数据上计算常用趋势、动量和波动率指标，用于生成信号和解释分析结论。</p>
      <div class="metric-grid">
        <div class="metric"><div class="metric-label">移动均线</div><div class="metric-value">MA5/10/20/30/60</div></div>
        <div class="metric"><div class="metric-label">MACD</div><div class="metric-value">12, 26, 9</div></div>
        <div class="metric"><div class="metric-label">RSI</div><div class="metric-value">周期 {{ config.rsi_period }}</div></div>
        <div class="metric"><div class="metric-label">布林带</div><div class="metric-value">20, 2.0</div></div>
        <div class="metric"><div class="metric-label">KDJ</div><div class="metric-value">9, 3, 3</div></div>
        <div class="metric"><div class="metric-label">ATR</div><div class="metric-value">周期 14</div></div>
      </div>
    </section>

    <section class="panel">
      <h2>观察信号规则</h2>
      <div class="rule-grid">
        <div>
          <h3>均线交叉</h3>
          <ul>
            <li>MA10 上穿 MA30：<span class="ok">趋势改善观察信号</span></li>
            <li>MA10 下穿 MA30：<span class="warn">趋势转弱复核信号</span></li>
          </ul>
        </div>
        <div>
          <h3>RSI 反转</h3>
          <ul>
            <li>RSI 从超卖区回升（&lt;{{ config.rsi_oversold }}）：<span class="ok">反弹观察信号</span></li>
            <li>RSI 从超买区回落（&gt;{{ config.rsi_overbought }}）：<span class="warn">过热回落复核信号</span></li>
          </ul>
        </div>
        <div>
          <h3>MACD 金叉/死叉</h3>
          <ul>
            <li>MACD 上穿 Signal：<span class="ok">买入</span></li>
            <li>MACD 下穿 Signal：<span class="warn">卖出</span></li>
          </ul>
        </div>
        <div>
          <h3>多策略投票</h3>
          <ul>
            <li>至少 2 个子策略看多：综合买入</li>
            <li>至少 2 个子策略看空：综合卖出</li>
          </ul>
        </div>
      </div>
    </section>

    <section class="panel">
      <h2>回测参数</h2>
      <div class="metric-grid">
        <div class="metric"><div class="metric-label">初始资金</div><div class="metric-value">{{ "{:,.0f}".format(config.initial_cash) }}</div></div>
        <div class="metric"><div class="metric-label">佣金</div><div class="metric-value">{{ "%.3f%%"|format(config.commission * 100) }}</div></div>
        <div class="metric"><div class="metric-label">滑点</div><div class="metric-value">{{ "%.2f%%"|format(config.slippage * 100) }}</div></div>
      </div>
    </section>

    <section class="panel">
      <h2>风控默认值</h2>
      <div class="metric-grid">
        <div class="metric"><div class="metric-label">单标的最大仓位</div><div class="metric-value">{{ "%.0f%%"|format(risk.max_position_pct * 100) }}</div></div>
        <div class="metric"><div class="metric-label">止损线</div><div class="metric-value">{{ "%.0f%%"|format(risk.stop_loss_pct * 100) }}</div></div>
        <div class="metric"><div class="metric-label">止盈线</div><div class="metric-value">{{ "%.0f%%"|format(risk.take_profit_pct * 100) }}</div></div>
        <div class="metric"><div class="metric-label">最大回撤警戒</div><div class="metric-value">{{ "%.0f%%"|format(risk.max_drawdown_pct * 100) }}</div></div>
        <div class="metric"><div class="metric-label">每日最大亏损</div><div class="metric-value">{{ "%.0f%%"|format(risk.max_daily_loss_pct * 100) }}</div></div>
        <div class="metric"><div class="metric-label">熔断动作</div><div class="metric-value">{{ risk.circuit_breaker_action }}</div></div>
        <div class="metric"><div class="metric-label">异常价格偏离</div><div class="metric-value">{{ "%.0f%%"|format(risk.max_order_price_deviation_pct * 100) }}</div></div>
        <div class="metric"><div class="metric-label">极端跌幅阈值</div><div class="metric-value">{{ "%.0f%%"|format(risk.max_extreme_move_pct * 100) }}</div></div>
        <div class="metric"><div class="metric-label">下单冷却</div><div class="metric-value">{{ risk.cooldown_minutes }} 分钟</div></div>
      </div>
    </section>

    <section class="panel">
      <h2>分析流程</h2>
      <div class="flow">
        <div class="flow-item">获取行情</div>
        <div class="flow-item">计算指标</div>
        <div class="flow-item">生成信号</div>
        <div class="flow-item">执行回测</div>
        <div class="flow-item">风控检查</div>
        <div class="flow-item">输出报告</div>
      </div>
    </section>
  </main>
</body>
</html>
"""

CLEAN_HISTORY_PAGE_TEMPLATE = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>经济历史 - AI 量化智能体</title>
  <style>
    :root { --bg:#eef1f4; --panel:#ffffff; --panel-2:#f7f9fb; --ink:#172033; --muted:#667085; --brand:#126e82; --line:#d9e0e7; --shadow:0 1px 2px rgba(16,24,40,.06); }
    * { box-sizing:border-box; }
    body { margin:0; font-family:"Microsoft YaHei","PingFang SC",Arial,sans-serif; color:var(--ink); background:var(--bg); min-height:100vh; font-size:14px; }
    .shell { max-width:1180px; margin:0 auto; padding:16px 20px 40px; }
    .back { display:inline-flex; padding:7px 12px; border-radius:6px; background:#fff; color:var(--brand); border:1px solid var(--line); text-decoration:none; font-weight:800; margin-bottom:12px; }
    .panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; box-shadow:var(--shadow); padding:20px; margin-bottom:12px; }
    .eyebrow { display:inline-flex; padding:4px 8px; border-radius:4px; background:#e6f4f1; color:var(--brand); font-size:11px; font-weight:800; text-transform:uppercase; }
    h1 { margin:10px 0 8px; font-size:30px; }
    h2 { margin:0 0 12px; font-size:18px; padding-bottom:10px; border-bottom:1px solid var(--line); }
    p,.muted { color:var(--muted); line-height:1.6; }
    .timeline { display:grid; gap:8px; }
    .event { padding:14px; border-radius:8px; background:var(--panel-2); border:1px solid var(--line); }
    .event strong { display:block; font-size:16px; margin-bottom:6px; }
    .tags { display:flex; flex-wrap:wrap; gap:8px; margin-top:10px; }
    .tag { padding:3px 6px; border-radius:4px; background:#e6f4f1; color:var(--brand); font-size:12px; font-weight:700; }
    .metric-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:0; border:1px solid var(--line); border-radius:8px; overflow:hidden; }
    .metric { padding:14px; background:#fff; border-right:1px solid var(--line); }
    .metric:last-child { border-right:0; }
    .metric-value { font-size:20px; font-weight:900; color:#0f172a; font-family:Consolas,"SFMono-Regular",monospace; }
    @media (max-width:800px) { .metric-grid { grid-template-columns:1fr; } .metric { border-right:0; border-bottom:1px solid var(--line); } h1 { font-size:26px; } .shell { padding:12px; } }
  </style>
</head>
<body>
  <main class="shell">
    <a class="back" href="{{ url_for('index') }}">返回控制台</a>
    <section class="panel">
      <div class="eyebrow">ECONOMIC HISTORY</div>
      <h1>经济历史与重大市场事件</h1>
      <p>这页用时间线梳理金融市场反复出现的主题：资产泡沫、信用扩张、政策转向、通胀冲击、技术浪潮和流动性变化。</p>
    </section>
    <section class="panel">
      <h2>估值观察指标</h2>
      <div class="metric-grid">
        {% for metric in valuation_metrics %}
        <article class="metric"><div class="muted">{{ metric.label }}</div><div class="metric-value">{{ metric.value }}</div><p>{{ metric.description }}</p></article>
        {% endfor %}
      </div>
    </section>
    <section class="panel">
      <h2>重大事件时间线</h2>
      <div class="timeline">
        {% for event in events %}
        <article class="event">
          <strong>{{ event.year }} · {{ event.title }}</strong>
          <p>{{ event.summary }}</p>
          <div class="tags">{% for tag in event.tags %}<span class="tag">{{ tag }}</span>{% endfor %}</div>
        </article>
        {% endfor %}
      </div>
    </section>
  </main>
</body>
</html>
"""

MARKET_REPORT_PAGE_TEMPLATE = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>市场日报/周报 - AI 量化智能体</title>
  <style>
    :root { --bg:#eef1f4; --panel:#ffffff; --panel-2:#f7f9fb; --ink:#172033; --muted:#667085; --brand:#126e82; --line:#d9e0e7; --ok:#087443; --warn:#b54708; --danger:#b42318; --shadow:0 1px 2px rgba(16,24,40,.06); }
    * { box-sizing:border-box; }
    body { margin:0; font-family:"Microsoft YaHei","PingFang SC",Arial,sans-serif; color:var(--ink); background:var(--bg); font-size:14px; }
    .shell { max-width:1240px; margin:0 auto; padding:16px 20px 40px; }
    .top { display:flex; justify-content:space-between; gap:10px; flex-wrap:wrap; align-items:center; margin-bottom:12px; }
    .panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; box-shadow:var(--shadow); padding:18px; margin-bottom:12px; }
    .grid { display:grid; grid-template-columns:340px 1fr; gap:12px; align-items:start; }
    .row { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
    h1 { margin:0 0 8px; font-size:28px; }
    h2 { margin:0 0 12px; font-size:18px; }
    p,.muted { color:var(--muted); line-height:1.6; }
    label { display:grid; gap:6px; color:#344054; font-weight:800; font-size:12px; margin-bottom:10px; }
    input,select,button { padding:9px 10px; border-radius:6px; border:1px solid #cfd7df; font:inherit; background:#fff; }
    button,.back,.chip { display:inline-flex; justify-content:center; align-items:center; padding:8px 12px; border-radius:6px; border:1px solid var(--line); text-decoration:none; font-weight:800; color:var(--brand); background:#fff; }
    button.primary { background:var(--brand); color:white; border-color:var(--brand); }
    .actions { display:flex; gap:8px; flex-wrap:wrap; align-items:center; }
    .notice { padding:10px 12px; border-radius:6px; background:#e6f4f1; border:1px solid #bfe4dc; color:#0f6f82; margin-bottom:12px; }
    .notice.error { background:#fff1f0; border-color:#ffd2cc; color:var(--danger); }
    .report { white-space:pre-wrap; background:#101828; color:#eef4ff; border-radius:8px; padding:14px; line-height:1.7; overflow:auto; max-height:760px; font-family:Consolas,"Microsoft YaHei",monospace; font-size:13px; }
    .kpis { display:grid; grid-template-columns:repeat(4,1fr); border:1px solid var(--line); border-radius:8px; overflow:hidden; margin:10px 0 12px; }
    .kpi { padding:12px; border-right:1px solid var(--line); background:var(--panel-2); }
    .kpi:last-child { border-right:0; }
    .kpi span { display:block; color:var(--muted); font-size:12px; font-weight:800; margin-bottom:4px; }
    .kpi strong { font-size:18px; }
    .list { display:grid; gap:8px; }
    .item { padding:12px; border:1px solid var(--line); border-radius:8px; background:var(--panel-2); }
    .item strong { display:block; margin-bottom:4px; }
    @media (max-width:900px) { .grid,.row,.kpis { grid-template-columns:1fr; } .kpi { border-right:0; border-bottom:1px solid var(--line); } .shell { padding:12px; } }
  </style>
</head>
<body>
  <main class="shell">
    <div class="top">
      <a class="back" href="{{ url_for('index') }}">返回控制台</a>
      <div class="actions">
        <form method="post"><input type="hidden" name="mode" value="market_report_run"><button class="primary" type="submit" name="report_type" value="daily">生成日报</button></form>
        <form method="post"><input type="hidden" name="mode" value="market_report_run"><button class="primary" type="submit" name="report_type" value="weekly">生成周报</button></form>
      </div>
    </div>
    {% if error %}<div class="notice error">{{ error }}</div>{% endif %}
    {% if note %}<div class="notice">{{ note }}</div>{% endif %}
    <section class="panel">
      <h1>市场日报/周报</h1>
      <p>自动汇总指数表现、板块强弱、资金流向、波动率、涨跌分布，并输出市场环境判断。</p>
    </section>
    <section class="grid">
      <div class="panel">
        <h2>自动生成</h2>
        {% set daily_job = (automations | selectattr('job_type','equalto','market_daily_report') | list | first) %}
        {% set weekly_job = (automations | selectattr('job_type','equalto','market_weekly_report') | list | first) %}
        <form method="post">
          <input type="hidden" name="mode" value="market_report_schedule">
          <label>生成时间 <input name="market_report_time" value="{{ daily_job.run_time if daily_job else '16:30' }}"></label>
          <label><span><input type="checkbox" name="market_daily_enabled" {% if daily_job and daily_job.enabled %}checked{% endif %} style="width:auto;margin-right:8px;">每日收盘后生成日报</span></label>
          <label><span><input type="checkbox" name="market_weekly_enabled" {% if weekly_job and weekly_job.enabled %}checked{% endif %} style="width:auto;margin-right:8px;">每周五生成周报</span></label>
          <div class="actions"><button class="primary" type="submit">保存市场报告计划</button></div>
        </form>
      </div>
      <div class="panel">
        {% if latest %}
        <h2>{{ latest.title }} · {{ latest.generated_at }}</h2>
        <div class="kpis">
          <div class="kpi"><span>环境</span><strong>{{ latest.environment.label }}</strong></div>
          <div class="kpi"><span>评分</span><strong>{{ latest.environment.score }}</strong></div>
          <div class="kpi"><span>指数均值</span><strong>{{ "%.2f%%"|format(latest.environment.avg_index_return) }}</strong></div>
          <div class="kpi"><span>上涨占比</span><strong>{{ "%.2f%%"|format(latest.environment.up_ratio) }}</strong></div>
        </div>
        <div class="report">{{ latest.text }}</div>
        {% else %}
        <h2>还没有市场报告</h2>
        <p class="muted">点击“生成日报”或“生成周报”后，这里会显示完整报告。</p>
        {% endif %}
      </div>
    </section>
    <section class="panel">
      <h2>历史报告</h2>
      {% if reports %}
      <div class="list">
        {% for report in reports %}
        <article class="item">
          <strong>{{ report.title }} · {{ report.generated_at }} · {{ report.environment.label }}</strong>
          <div class="muted">评分 {{ report.environment.score }}｜指数均值 {{ "%.2f%%"|format(report.environment.avg_index_return) }}｜上涨占比 {{ "%.2f%%"|format(report.environment.up_ratio) }}</div>
        </article>
        {% endfor %}
      </div>
      {% else %}
      <p class="muted">暂无历史报告。</p>
      {% endif %}
    </section>
  </main>
</body>
</html>
"""


RESEARCH_REPORT_PAGE_TEMPLATE = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>投资复盘报告 - AI 投资复盘助手</title>
  <style>
    :root { --bg:#eef1f4; --panel:#fff; --ink:#172033; --muted:#667085; --brand:#126e82; --line:#d9e0e7; --danger:#b42318; }
    * { box-sizing:border-box; }
    body { margin:0; font-family:"Microsoft YaHei","PingFang SC",Arial,sans-serif; background:var(--bg); color:var(--ink); font-size:14px; }
    .shell { max-width:1180px; margin:0 auto; padding:16px 20px 42px; }
    .top { display:flex; justify-content:space-between; gap:10px; flex-wrap:wrap; align-items:center; margin-bottom:12px; }
    .panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:18px; margin-bottom:12px; }
    h1 { margin:0 0 8px; font-size:28px; } h2 { margin:0 0 12px; font-size:18px; }
    p,.muted { color:var(--muted); line-height:1.6; }
    .grid { display:grid; grid-template-columns:340px 1fr; gap:12px; align-items:start; }
    label { display:grid; gap:6px; font-weight:800; color:#344054; margin-bottom:10px; }
    input,select,button { padding:9px 10px; border-radius:6px; border:1px solid #cfd7df; font:inherit; background:#fff; }
    button,.btn { display:inline-flex; justify-content:center; align-items:center; padding:8px 12px; border-radius:6px; border:1px solid var(--line); text-decoration:none; font-weight:800; color:var(--brand); background:#fff; cursor:pointer; }
    button.primary,.btn.primary { background:var(--brand); color:#fff; border-color:var(--brand); }
    .actions { display:flex; gap:8px; flex-wrap:wrap; }
    .notice { padding:10px 12px; border-radius:6px; background:#e6f4f1; border:1px solid #bfe4dc; color:#0f6f82; margin-bottom:12px; }
    .notice.error { background:#fff1f0; border-color:#ffd2cc; color:var(--danger); }
    .report { white-space:pre-wrap; background:#101828; color:#eef4ff; border-radius:8px; padding:14px; line-height:1.72; overflow:auto; max-height:760px; font-family:Consolas,"Microsoft YaHei",monospace; font-size:13px; }
    .list { display:grid; gap:8px; }
    .item { padding:12px; border:1px solid var(--line); border-radius:8px; background:#f7f9fb; }
    .item strong { display:block; margin-bottom:5px; }
    @media (max-width:900px) { .grid { grid-template-columns:1fr; } .shell { padding:12px; } }
  </style>
</head>
<body>
  <main class="shell">
    <div class="top"><a class="btn" href="{{ url_for('index') }}">返回控制台</a><a class="btn" href="{{ url_for('analysis_page') }}">去分析台</a></div>
    {% if error %}<div class="notice error">{{ error }}</div>{% endif %}
    {% if note %}<div class="notice">{{ note }}</div>{% endif %}
    <section class="panel">
      <h1>投资复盘报告</h1>
      <p>上传持仓、净值或交易记录，生成看得懂、可追溯、重风险的复盘报告。报告用于观察、复核和预警，不提供直接买卖指令。</p>
    </section>
    <section class="grid">
      <div class="panel">
        <h2>上传持仓 / 净值 / 交易记录</h2>
        <form method="post" enctype="multipart/form-data">
          <input type="hidden" name="mode" value="upload_report">
          <label>数据文件 <input type="file" name="data_file" accept=".csv,.xlsx,.xls" required></label>
          <button class="primary" type="submit">生成投资复盘报告</button>
        </form>
        {% if history %}
        <div class="actions" style="margin-top:12px;">
          <a class="btn primary" href="{{ url_for('download_history_research_report', item_index=0, fmt='pdf') }}">从最近分析导出 PDF</a>
          <a class="btn" href="{{ url_for('download_history_research_report', item_index=0, fmt='docx') }}">Word</a>
          <a class="btn" href="{{ url_for('download_history_research_report', item_index=0, fmt='md') }}">Markdown</a>
        </div>
        {% endif %}
        <p class="muted">建议字段：date、nav/净值、close/收盘、return/收益率、symbol/代码、quantity/数量、avg_cost/成本、weight/权重、pnl/盈亏。</p>
      </div>
      <div class="panel">
        {% if latest %}
        <h2>{{ latest.title }}</h2>
        <div class="actions" style="margin-bottom:12px;">
          <a class="btn primary" href="{{ url_for('download_research_report', report_id=latest.id, fmt='md') }}">Markdown</a>
          <a class="btn primary" href="{{ url_for('download_research_report', report_id=latest.id, fmt='pdf') }}">PDF</a>
          <a class="btn primary" href="{{ url_for('download_research_report', report_id=latest.id, fmt='docx') }}">Word</a>
        </div>
        <div class="report">{{ latest.markdown }}</div>
        {% else %}
        <h2>暂无报告</h2>
        <p class="muted">上传数据或完成一次标的分析后，会自动生成投资复盘与风险报告。</p>
        {% endif %}
      </div>
    </section>
    <section class="panel">
      <h2>历史复盘报告</h2>
      {% if reports %}
      <div class="list">
        {% for report in reports %}
        <article class="item">
          <strong>{{ report.title }} · {{ report.generated_at }}</strong>
          <div class="actions">
            <a class="btn" href="{{ url_for('download_research_report', report_id=report.id, fmt='md') }}">Markdown</a>
            <a class="btn" href="{{ url_for('download_research_report', report_id=report.id, fmt='pdf') }}">PDF</a>
            <a class="btn" href="{{ url_for('download_research_report', report_id=report.id, fmt='docx') }}">Word</a>
          </div>
        </article>
        {% endfor %}
      </div>
      {% else %}<p class="muted">暂无历史报告。</p>{% endif %}
    </section>
  </main>
</body>
</html>
"""


RESEARCH_REPORT_PAGE_TEMPLATE = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>投资复盘报告 - AI 投资复盘助手</title>
  <style>
    :root { --bg:#f5f8fb; --panel:#fff; --ink:#101828; --muted:#667085; --line:#e2e8f0; --brand:#078894; --brand2:#11a7a3; --blue:#2684ff; --purple:#7658e8; --orange:#f28a16; --green:#10a66a; --red:#ef3340; --shadow:0 14px 36px rgba(16,24,40,.07),0 1px 2px rgba(16,24,40,.05); }
    * { box-sizing:border-box; }
    body { margin:0; min-height:100vh; font-family:"Microsoft YaHei","PingFang SC",Arial,sans-serif; color:var(--ink); background:radial-gradient(circle at 85% 0,rgba(7,136,148,.08),transparent 25%),var(--bg); font-size:14px; }
    a { color:inherit; text-decoration:none; }
    .app { min-height:100vh; display:grid; grid-template-columns:252px minmax(0,1fr); }
    .sidebar { position:sticky; top:0; height:100vh; padding:18px; background:rgba(255,255,255,.94); border-right:1px solid var(--line); display:flex; flex-direction:column; gap:18px; }
    .brand { display:flex; align-items:center; gap:14px; padding:0 8px 14px; border-bottom:1px solid var(--line); }
    .brand-mark { width:48px; height:48px; border-radius:12px; display:grid; place-items:center; color:#fff; background:linear-gradient(135deg,var(--brand),var(--brand2)); box-shadow:0 14px 28px rgba(7,136,148,.28); font:900 25px Consolas,monospace; }
    .brand-title { font-size:24px; font-weight:900; }
    .nav { display:grid; gap:8px; }
    .nav a { display:flex; align-items:center; gap:12px; padding:13px 14px; border-radius:10px; color:#263856; font-weight:800; }
    .nav a:hover,.nav a.active { color:#fff; background:linear-gradient(135deg,var(--brand),#0a7184); box-shadow:0 12px 26px rgba(7,136,148,.24); }
    .ico { width:20px; text-align:center; }
    .system-card { margin-top:auto; padding:14px; border:1px solid var(--line); border-radius:12px; background:#fff; box-shadow:0 8px 20px rgba(16,24,40,.04); }
    .system-row { display:flex; justify-content:space-between; gap:8px; padding:8px 0; color:#52637a; font-size:12px; border-bottom:1px solid #eef2f6; }
    .system-row:last-child { border-bottom:0; }
    .dot { width:8px; height:8px; border-radius:999px; background:#16c784; display:inline-block; margin-right:6px; }
    .main { min-width:0; }
    .topbar { min-height:76px; padding:14px 28px; display:flex; justify-content:space-between; align-items:center; gap:18px; background:rgba(255,255,255,.88); border-bottom:1px solid var(--line); backdrop-filter:blur(16px); }
    .market-status { display:flex; align-items:center; gap:18px; padding:10px 16px; border:1px solid var(--line); border-radius:10px; background:#fff; box-shadow:0 8px 18px rgba(16,24,40,.04); color:#40516b; font-size:13px; white-space:nowrap; overflow:auto; }
    .market-status strong { color:var(--green); font-family:Consolas,monospace; }
    .top-actions { display:flex; align-items:center; gap:12px; }
    .icon-btn,.tool-btn,button,.btn { display:inline-flex; align-items:center; justify-content:center; border-radius:10px; border:1px solid var(--line); background:#fff; color:#52637a; font-weight:800; }
    .icon-btn { width:36px; height:36px; position:relative; }
    .tool-btn,button,.btn { padding:9px 12px; cursor:pointer; font:inherit; }
    .primary { background:linear-gradient(135deg,var(--brand),var(--brand2)); color:#fff; border:0; }
    .user-chip { display:flex; align-items:center; gap:10px; color:#263856; font-weight:900; }
    .avatar { width:34px; height:34px; border-radius:999px; background:#9aa8bd; display:grid; place-items:center; color:#fff; }
    .content { padding:24px 28px 34px; display:grid; gap:18px; }
    .page-head { display:flex; justify-content:space-between; gap:16px; align-items:center; }
    h1 { margin:0; font-size:28px; letter-spacing:0; }
    h2 { margin:0; font-size:16px; letter-spacing:0; }
    p,.muted { color:var(--muted); line-height:1.65; }
    .panel { background:rgba(255,255,255,.92); border:1px solid var(--line); border-radius:12px; box-shadow:var(--shadow); }
    .panel-pad { padding:18px; }
    .panel-head { padding:16px 18px 0; display:flex; justify-content:space-between; gap:12px; align-items:center; }
    .report-grid { display:grid; grid-template-columns:360px minmax(0,1fr); gap:14px; align-items:start; }
    .form-panel { display:grid; gap:14px; }
    label { display:grid; gap:7px; color:#263856; font-weight:800; }
    input,select,textarea { width:100%; min-height:42px; padding:9px 10px; border-radius:9px; border:1px solid #cfd7df; background:#fff; font:inherit; color:var(--ink); }
    textarea { min-height:82px; resize:vertical; }
    .flow-card { padding:14px; border:1px solid #dbeafe; border-radius:10px; background:#eff6ff; display:grid; gap:8px; }
    .flow-card b { color:#174ea6; }
    .template-links { display:grid; gap:8px; }
    .template-links .btn { justify-content:flex-start; }
    .actions { display:flex; gap:8px; flex-wrap:wrap; align-items:center; }
    .notice { padding:11px 13px; border-radius:10px; background:#e6f7f6; border:1px solid #9bd7d3; color:#0f6f82; font-weight:800; }
    .notice.error { background:#fff1f0; border-color:#ffd2cc; color:var(--red); }
    .reader { min-height:520px; }
    .reader-head { padding:18px 18px 0; display:flex; justify-content:space-between; gap:12px; align-items:flex-start; flex-wrap:wrap; }
    .report { margin:16px 18px 18px; white-space:pre-wrap; background:#fff; color:#1f2937; border:1px solid var(--line); border-left:4px solid var(--brand); border-radius:10px; padding:16px; line-height:1.78; overflow:auto; max-height:720px; font-family:Consolas,"Microsoft YaHei",monospace; font-size:13px; }
    .followup-panel { margin:16px 18px 0; padding:14px; border:1px solid #bfdbfe; border-radius:10px; background:#eff6ff; display:grid; gap:10px; }
    .followup-panel textarea { width:100%; min-height:82px; padding:10px; border:1px solid #cfd7df; border-radius:9px; resize:vertical; font:inherit; }
    .followup-output { display:grid; gap:8px; max-height:260px; overflow:auto; }
    .followup-message { padding:10px 12px; border:1px solid var(--line); border-radius:8px; background:#fff; color:#344054; line-height:1.65; white-space:pre-wrap; }
    .followup-message.user { background:#f8fafc; font-weight:800; }
    .history-list { display:grid; gap:10px; padding:10px 18px 18px; }
    .history-item { display:grid; grid-template-columns:minmax(0,1fr) auto; gap:12px; align-items:center; padding:12px 0; border-bottom:1px solid #edf2f7; }
    .history-item:last-child { border-bottom:0; }
    .history-item strong { display:block; margin-bottom:4px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    .empty { padding:36px 18px; color:var(--muted); }
    @media (max-width:1280px) { .app { grid-template-columns:1fr; } .sidebar { position:static; height:auto; } .nav { grid-template-columns:repeat(4,1fr); } .topbar { height:auto; flex-wrap:wrap; padding:14px; } .report-grid { grid-template-columns:1fr; } }
    @media (max-width:720px) { .content { padding:16px; } .page-head,.history-item,.reader-head { display:grid; grid-template-columns:1fr; } .market-status { flex-wrap:wrap; } .nav { grid-template-columns:1fr 1fr; } }
  </style>
</head>
<body>
  <div class="app">
    <aside class="sidebar">
      <div class="brand"><span class="brand-mark">R</span><span class="brand-title">投资复盘助手</span></div>
      <nav class="nav">
        <a href="{{ url_for('index') }}"><span class="ico">▥</span>资产总览</a>
        <a href="{{ url_for('analysis_page') }}"><span class="ico">⌁</span>分析台</a>
        <a href="{{ url_for('backtest_compare') }}"><span class="ico">⌘</span>历史表现复盘</a>
        <a href="{{ url_for('economic_history') }}"><span class="ico">⌇</span>经济历史</a>
        <a href="{{ url_for('portfolio_page') }}"><span class="ico">▣</span>组合管理</a>
        <a href="{{ url_for('alerts_page') }}"><span class="ico">◇</span>价格预警</a>
        <a href="{{ url_for('automation_page') }}"><span class="ico">▧</span>自动化任务</a>
        <a href="{{ url_for('analysis_history_page') }}"><span class="ico">◷</span>历史复盘</a>
        <a href="{{ url_for('market_report') }}"><span class="ico">▤</span>市场报告</a>
        <a class="active" href="{{ url_for('research_report_page') }}"><span class="ico">▦</span>复盘报告</a>
      </nav>
      <div class="system-card">
        <div class="system-row"><span>系统状态</span><span><i class="dot"></i>正常运行</span></div>
        <div class="system-row"><span>报告模块</span><span>Markdown / PDF / Word</span></div>
      </div>
    </aside>
    <main class="main">
      <header class="topbar">
        <div class="market-status"><span>报告中心 <i class="dot"></i> 可导出</span><span>投资复盘报告</span><span>最近报告 <strong>{{ reports|length }}</strong></span></div>
        <div class="top-actions">
          <a class="tool-btn" href="{{ url_for('analysis_page') }}">去分析台</a>
          <a class="tool-btn" href="{{ url_for('index') }}">返回控制台</a>
          {% if current_user %}<span class="user-chip"><span class="avatar">●</span>{{ current_user }}</span><form method="post" action="{{ url_for('logout') }}"><button type="submit">退出</button></form>{% endif %}
        </div>
      </header>
      <section class="content">
        <div class="page-head">
          <div><h1>投资复盘与风险报告</h1><p class="muted">上传持仓、净值或交易记录，整理过去表现、回撤风险、集中度和下一步观察清单。</p></div>
          <div class="actions"><a class="btn" href="{{ url_for('analysis_history_page') }}">历史复盘</a><a class="btn primary" href="{{ url_for('research_report_page') }}">上传生成报告</a></div>
        </div>
        {% if error %}<div class="notice error">{{ error }}</div>{% endif %}
        {% if note %}<div class="notice">{{ note }}</div>{% endif %}
        <section class="report-grid">
          <div class="panel panel-pad form-panel">
            <h2>上传数据生成复盘报告</h2>
            <div class="flow-card">
              <b>推荐流程</b>
              <span class="muted">选择报告类型 → 上传持仓/净值/交易记录 → 查看风险解释 → 按观察清单补数/复核 → 导出报告。</span>
            </div>
            <form method="post" enctype="multipart/form-data">
              <input type="hidden" name="mode" value="upload_report">
              <label>报告类型
                <select name="report_type">
                  <option>个人持仓体检报告</option>
                  <option>基金/ETF 分析报告</option>
                  <option>小资金组合风险报告</option>
                  <option>交易复盘报告</option>
                  <option>亏损原因分析报告</option>
                  <option>定投/补仓观察报告</option>
                  <option>每周账户复盘报告</option>
                </select>
              </label>
              <label>读者版本
                <select name="audience">
                  <option>个人投资者版</option>
                  <option>小资金账户版</option>
                  <option>业余量化版</option>
                  <option>小型投研团队版</option>
                </select>
              </label>
              <label>本次报告要解决什么问题
                <textarea name="objective" placeholder="例如：看这只基金最近是否变差；复核组合是否过于集中；分析最近亏损可能来自哪里。"></textarea>
              </label>
              <label>数据文件 <input type="file" name="data_file" accept=".csv,.xlsx,.xls" required></label>
              <button class="primary" type="submit">生成投资复盘报告</button>
            </form>
            <form method="post" action="{{ url_for('create_sample_research_report') }}">
              <input type="hidden" name="report_type" value="基金/ETF 分析报告">
              <input type="hidden" name="audience" value="个人投资者版">
              <input type="hidden" name="objective" value="演示报告如何从净值曲线解释过去表现、回撤风险和下一步观察清单">
              <button type="submit">没有数据，先生成示例报告</button>
            </form>
            <div class="template-links">
              <a class="btn" href="{{ url_for('download_research_template') }}">下载 CSV 数据模板</a>
            </div>
            {% if history %}
            <div class="actions">
              <a class="btn primary" href="{{ url_for('download_history_research_report', item_index=0, fmt='pdf') }}">从最近分析导出 PDF</a>
              <a class="btn" href="{{ url_for('download_history_research_report', item_index=0, fmt='docx') }}">Word</a>
              <a class="btn" href="{{ url_for('download_history_research_report', item_index=0, fmt='md') }}">Markdown</a>
            </div>
            {% endif %}
            <p class="muted">最低可用字段：date + nav/close/return。持仓体检建议补充 symbol、quantity、avg_cost、weight；交易复盘建议补充 pnl、买入日期、卖出日期和手续费。</p>
          </div>
          <div class="panel reader">
            {% if latest %}
            <div class="reader-head">
              <div><h2>{{ latest.title }}</h2><p class="muted">{{ latest.generated_at }}</p></div>
              <div class="actions">
                <a class="btn primary" href="{{ url_for('download_research_report', report_id=latest.id, fmt='md') }}">Markdown</a>
                <a class="btn primary" href="{{ url_for('download_research_report', report_id=latest.id, fmt='pdf') }}">PDF</a>
                <a class="btn primary" href="{{ url_for('download_research_report', report_id=latest.id, fmt='docx') }}">Word</a>
              </div>
            </div>
            <div class="followup-panel" data-followup-card data-report-id="{{ latest.id }}">
              <strong>继续追问报告</strong>
              <textarea class="followup-question" placeholder="例如：这次亏损可能来自哪里？如果继续跌我可能承受什么？下一步该观察什么？"></textarea>
              <div class="actions"><button type="button" class="primary followup-send">发送追问</button></div>
              <div class="followup-output"></div>
            </div>
            <div class="report" data-followup-context>{{ latest.markdown }}</div>
            {% else %}
            <div class="empty"><h2>暂无报告</h2><p>上传持仓、净值或交易记录后，这里会显示投资复盘与风险报告。</p></div>
            {% endif %}
          </div>
        </section>
        <section class="panel">
          <div class="panel-head"><h2>历史复盘报告</h2></div>
          {% if reports %}
          <div class="history-list">
            {% for report in reports %}
            <article class="history-item">
              <div><strong>{{ report.title }} · {{ report.generated_at }}</strong><span class="muted">{{ report.subject if report.subject else report.id }}</span></div>
              <div class="actions">
                <a class="btn" href="{{ url_for('download_research_report', report_id=report.id, fmt='md') }}">Markdown</a>
                <a class="btn" href="{{ url_for('download_research_report', report_id=report.id, fmt='pdf') }}">PDF</a>
                <a class="btn" href="{{ url_for('download_research_report', report_id=report.id, fmt='docx') }}">Word</a>
              </div>
            </article>
            {% endfor %}
          </div>
          {% else %}<div class="empty">暂无历史报告。</div>{% endif %}
        </section>
      </section>
    </main>
  </div>
  <div class="explain-modal" id="explainModal" role="dialog" aria-modal="true" aria-labelledby="explainTitle">
    <div class="explain-dialog">
      <div class="explain-head"><strong id="explainTitle">指标解释</strong><button type="button" class="explain-close" aria-label="关闭">×</button></div>
      <div class="explain-body" id="explainBody">正在加载...</div>
    </div>
  </div>
  <script>
    function appendFollowupMessage(box, text, cls) {
      const node = document.createElement('div');
      node.className = `followup-message ${cls || ''}`.trim();
      node.textContent = text;
      box.appendChild(node);
      box.scrollTop = box.scrollHeight;
    }
    document.querySelectorAll('[data-followup-card]').forEach(card => {
      const output = card.querySelector('.followup-output');
      const textarea = card.querySelector('.followup-question');
      const reportId = card.dataset.reportId || '';
      const contextNode = document.querySelector('[data-followup-context]');
      card.querySelector('.followup-send')?.addEventListener('click', async () => {
        const question = (textarea?.value || '').trim();
        if (!question) return;
        appendFollowupMessage(output, question, 'user');
        textarea.value = '';
        appendFollowupMessage(output, 'Agent 正在分析...', '');
        const waitingNode = output.lastElementChild;
        const formData = new FormData();
        formData.append('csrf_token', '{{ csrf_token() }}');
        formData.append('question', question);
        formData.append('report_id', reportId);
        formData.append('context', contextNode?.textContent || '');
        try {
          const res = await fetch('{{ url_for("report_followup_api") }}', { method:'POST', body:formData });
          const data = await res.json();
          waitingNode.textContent = data.ok ? data.answer : (data.error || '追问失败，请稍后重试。');
        } catch (err) {
          waitingNode.textContent = '追问失败，请检查 API 配置或稍后重试。';
        }
      });
    });
  </script>
</body>
</html>
"""


UI_CONCEPTS_TEMPLATE = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>UI 定稿候选 - 10 版量化投研界面</title>
  <style>
    :root { --bg:#eef2f6; --ink:#121826; --muted:#667085; --line:#d8e0e8; --brand:#0f6f82; --green:#16a34a; --red:#dc2626; --amber:#d97706; }
    * { box-sizing:border-box; }
    body { margin:0; font-family:"Microsoft YaHei","PingFang SC",Arial,sans-serif; background:var(--bg); color:var(--ink); }
    .top { position:sticky; top:0; z-index:5; display:flex; justify-content:space-between; align-items:center; gap:16px; padding:14px 22px; background:rgba(255,255,255,.94); border-bottom:1px solid var(--line); backdrop-filter:blur(14px); }
    .brand { display:flex; align-items:center; gap:10px; font-weight:900; }
    .mark { width:32px; height:32px; border-radius:9px; display:grid; place-items:center; color:#fff; background:linear-gradient(135deg,#0f6f82,#0d9488); font-family:Consolas,monospace; }
    .top a { color:var(--brand); text-decoration:none; font-weight:800; padding:8px 12px; border:1px solid var(--line); border-radius:8px; background:#fff; }
    .intro { max-width:1440px; margin:0 auto; padding:22px; display:grid; gap:8px; }
    h1 { margin:0; font-size:30px; }
    .intro p { margin:0; color:var(--muted); line-height:1.7; }
    .grid { max-width:1440px; margin:0 auto; padding:0 22px 40px; display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:18px; }
    .concept { background:#fff; border:1px solid var(--line); border-radius:16px; overflow:hidden; box-shadow:0 18px 48px rgba(16,24,40,.08); }
    .concept-head { padding:14px 16px; border-bottom:1px solid var(--line); display:flex; justify-content:space-between; gap:12px; align-items:flex-start; }
    .concept h2 { margin:0 0 4px; font-size:18px; }
    .concept p { margin:0; color:var(--muted); line-height:1.55; font-size:13px; }
    .badge { white-space:nowrap; padding:5px 8px; border-radius:999px; background:#e6f4f1; color:#0f6f82; font-size:12px; font-weight:900; }
    .mock { height:390px; padding:14px; display:grid; gap:10px; overflow:hidden; }
    .bar,.panel,.tile,.chart,.table,.rail,.hero,.side { border-radius:10px; }
    .bar { display:flex; align-items:center; justify-content:space-between; gap:8px; padding:8px 10px; font-size:12px; font-weight:800; }
    .mini { display:flex; gap:8px; flex-wrap:wrap; }
    .pill { padding:5px 8px; border-radius:999px; font-size:11px; font-weight:900; }
    .panel,.tile { padding:10px; }
    .metric { font-family:Consolas,monospace; font-weight:900; font-size:20px; }
    .label { color:inherit; opacity:.62; font-size:11px; font-weight:800; }
    .chart { position:relative; min-height:120px; overflow:hidden; }
    .chart::before { content:""; position:absolute; inset:0; background:linear-gradient(transparent 24px,rgba(148,163,184,.18) 25px),linear-gradient(90deg,transparent 44px,rgba(148,163,184,.16) 45px); background-size:100% 25px,45px 100%; }
    .chart::after { content:""; position:absolute; left:18px; right:18px; top:34px; height:78px; border-bottom:4px solid currentColor; border-right:4px solid currentColor; transform:skew(-22deg) rotate(-5deg); opacity:.85; border-radius:0 0 14px 0; }
    .table { display:grid; gap:0; overflow:hidden; }
    .row { display:grid; grid-template-columns:1.2fr .8fr .8fr; gap:8px; padding:8px 10px; border-bottom:1px solid rgba(148,163,184,.24); font-size:12px; align-items:center; }
    .row:last-child { border-bottom:0; }
    .up { color:#16a34a; } .down { color:#dc2626; } .warn { color:#d97706; }
    .c1 .mock { background:#070b12; color:#dbeafe; grid-template-columns:86px 1.1fr .9fr; grid-template-rows:40px 1fr 1fr; }
    .c1 .bar { grid-column:1/-1; background:#101828; border:1px solid #273449; }
    .c1 .rail { grid-row:2/4; background:#101828; border:1px solid #273449; display:grid; align-content:start; gap:8px; padding:10px; color:#94a3b8; font-size:12px; font-weight:900; }
    .c1 .chart,.c1 .panel,.c1 .table { background:#101828; border:1px solid #273449; color:#22d3ee; }
    .c1 .table { color:#dbeafe; }
    .c2 .mock { background:#f7fafc; grid-template-columns:1.1fr .9fr; grid-template-rows:42px 92px 1fr; }
    .c2 .bar { grid-column:1/-1; background:#fff; border:1px solid #d8e0e8; }
    .c2 .mini { grid-column:1/-1; display:grid; grid-template-columns:repeat(4,1fr); gap:8px; }
    .c2 .tile,.c2 .chart,.c2 .table { background:#fff; border:1px solid #d8e0e8; color:#0f6f82; }
    .c3 .mock { background:#0b1020; color:#e5e7eb; grid-template-columns:64px 1fr 220px; grid-template-rows:40px 1fr; }
    .c3 .bar { grid-column:1/-1; background:#111827; border:1px solid #2b3548; }
    .c3 .rail,.c3 .side,.c3 .chart { background:#111827; border:1px solid #2b3548; }
    .c3 .rail { display:grid; place-items:center; color:#94a3b8; font-weight:900; }
    .c3 .chart { color:#22c55e; min-height:300px; }
    .c4 .mock { background:#f2f5f8; grid-template-columns:250px 1fr; grid-template-rows:42px 1fr 110px; }
    .c4 .bar { grid-column:1/-1; background:#172033; color:#fff; }
    .c4 .side,.c4 .chart,.c4 .panel { background:#fff; border:1px solid #d8e0e8; color:#2563eb; }
    .c4 .panel { grid-column:1/-1; color:#172033; }
    .c5 .mock { background:#fff7ed; grid-template-columns:repeat(3,1fr); grid-template-rows:42px 100px 1fr; }
    .c5 .bar { grid-column:1/-1; background:#431407; color:#fed7aa; }
    .c5 .tile,.c5 .chart,.c5 .table { background:#fff; border:1px solid #fed7aa; color:#b45309; }
    .c5 .chart { grid-column:1/3; }
    .c6 .mock { background:#f8fafc; grid-template-columns:1fr 1fr; grid-template-rows:42px 92px 1fr; }
    .c6 .bar { grid-column:1/-1; background:#fff; border:1px solid #d8e0e8; }
    .c6 .mini { grid-column:1/-1; display:grid; grid-template-columns:repeat(3,1fr); gap:8px; }
    .c6 .tile,.c6 .chart,.c6 .table { background:#fff; border:1px solid #d8e0e8; color:#475569; }
    .c7 .mock { background:#eef6ff; grid-template-columns:240px 1fr; grid-template-rows:42px 1fr 115px; }
    .c7 .bar { grid-column:1/-1; background:#0f172a; color:#bfdbfe; }
    .c7 .side,.c7 .chart,.c7 .table { background:#fff; border:1px solid #bfdbfe; color:#2563eb; }
    .c7 .table { grid-column:1/-1; }
    .c8 .mock { background:#f4f1ea; grid-template-columns:1fr 1fr 1fr; grid-template-rows:42px 1fr 1fr; }
    .c8 .bar { grid-column:1/-1; background:#1c1917; color:#fde68a; }
    .c8 .chart,.c8 .panel,.c8 .tile { background:#fffaf0; border:1px solid #e7d7bd; color:#92400e; }
    .c8 .chart { grid-column:1/3; grid-row:2/4; }
    .c9 .mock { background:#0f172a; color:#e2e8f0; grid-template-columns:1fr 250px; grid-template-rows:42px 1fr 120px; }
    .c9 .bar { grid-column:1/-1; background:#020617; border:1px solid #334155; }
    .c9 .hero,.c9 .side,.c9 .table { background:#111827; border:1px solid #334155; color:#a7f3d0; }
    .c9 .hero { grid-row:2/4; }
    .c10 .mock { background:#f9fafb; grid-template-columns:1fr 1fr; grid-template-rows:42px 1fr 1fr; }
    .c10 .bar { grid-column:1/-1; background:#fff; border:1px solid #d8e0e8; }
    .c10 .hero { grid-row:2/4; background:linear-gradient(135deg,#0f172a,#0f6f82); color:#fff; }
    .c10 .tile,.c10 .table { background:#fff; border:1px solid #d8e0e8; color:#0f172a; }
    @media (max-width:980px) { .grid { grid-template-columns:1fr; } .mock { height:auto; min-height:430px; } }
  </style>
</head>
<body>
  <div class="top"><div class="brand"><span class="mark">Q</span><span>10 版 UI 定稿候选</span></div><a href="{{ url_for('index') }}">返回当前首页</a></div>
  <section class="intro"><h1>量化投研系统 UI 方向提案</h1><p>每一版都按真实工作流设计：分析输入、图表结果、持仓、风险、历史复盘、自动化入口。你选方向后，我会把主界面按那一版精修落地。</p></section>
  <main class="grid">
    <article class="concept c1"><div class="concept-head"><div><h2>01 复盘工作台版</h2><p>适合查看图表、日志、观察信号和风险状态，但不做重型交易终端。</p></div><span class="badge">复盘优先</span></div><div class="mock"><div class="bar"><span>投资复盘助手</span><span class="up">风险跟踪</span></div><div class="rail">复盘<br>组合<br>风险<br>任务</div><div class="chart"></div><div class="table"><div class="row"><b>标的</b><b>观察</b><b>收益</b></div><div class="row"><span>000001</span><span class="up">趋势改善</span><span>+3.2%</span></div><div class="row"><span>NVDA</span><span class="warn">继续观察</span><span>-1.1%</span></div></div><div class="panel"><span class="label">AI 结论</span><div class="metric">偏强 / 中风险</div></div><div class="panel"><span class="label">回撤</span><div class="metric down">-6.8%</div></div></div></article>
    <article class="concept c2"><div class="concept-head"><div><h2>02 资产仪表盘版</h2><p>指标、列表、图表平衡，适合日常投研和组合复盘。</p></div><span class="badge">最均衡</span></div><div class="mock"><div class="bar"><span>研究总览</span><span>导出 / 任务 / 设置</span></div><div class="mini"><div class="tile"><span class="label">持仓</span><div class="metric">13</div></div><div class="tile"><span class="label">胜率</span><div class="metric up">61%</div></div><div class="tile"><span class="label">缓存</span><div class="metric">5</div></div><div class="tile"><span class="label">风险</span><div class="metric warn">中</div></div></div><div class="chart"></div><div class="table"><div class="row"><b>资产</b><b>价格</b><b>评级</b></div><div class="row"><span>002982</span><span>1.02</span><span class="up">A</span></div><div class="row"><span>BTC</span><span>92K</span><span>B</span></div></div></div></article>
    <article class="concept c3"><div class="concept-head"><div><h2>03 图表优先版</h2><p>主图表画布最大，技术图表和收益曲线放到第一视觉层级。</p></div><span class="badge">图表核心</span></div><div class="mock"><div class="bar"><span>002982 · max</span><span class="mini"><span class="pill">MA</span><span class="pill">RSI</span><span class="pill">MACD</span></span></div><div class="rail">工具</div><div class="chart"></div><div class="side"><div class="panel"><span class="label">观察信号</span><div class="metric up">改善</div></div><div class="panel"><span class="label">样本</span><div class="metric">1024</div></div></div></div></article>
    <article class="concept c4"><div class="concept-head"><div><h2>04 研究实验室版</h2><p>适合业余量化复核参数、历史表现和实验记录。</p></div><span class="badge">研发导向</span></div><div class="mock"><div class="bar"><span>复盘实验室</span><span>Observe → Review → Report</span></div><div class="side"><b>参数面板</b><p>市场、周期、滑点、费用、风险阈值</p></div><div class="chart"></div><div class="panel"><span class="label">实验日志</span><div class="row"><span>MA10/30</span><span class="up">可观察</span><span>回撤 18%</span></div></div></div></article>
    <article class="concept c5"><div class="concept-head"><div><h2>05 风险复核中心版</h2><p>把风险、预警、回撤、仓位暴露放在核心位置，适合日常复盘。</p></div><span class="badge">风控优先</span></div><div class="mock"><div class="bar"><span>风险复核中心</span><span class="warn">3 条预警</span></div><div class="tile"><span class="label">组合回撤</span><div class="metric down">-8.4%</div></div><div class="tile"><span class="label">现金占比</span><div class="metric">21%</div></div><div class="tile"><span class="label">风险状态</span><div class="metric warn">监控中</div></div><div class="chart"></div><div class="table"><div class="row"><b>预警</b><b>条件</b><b>状态</b></div><div class="row"><span>002982</span><span>≤0.85</span><span class="warn">接近</span></div></div></div></article>
    <article class="concept c6"><div class="concept-head"><div><h2>06 组合体检版</h2><p>以持仓和资产配置为中心，适合每天看组合、集中度和导出复盘报告。</p></div><span class="badge">组合管理</span></div><div class="mock"><div class="bar"><span>组合体检台</span><span>日报 / 导出 / 复核</span></div><div class="mini"><div class="tile"><span class="label">总资产</span><div class="metric">¥128K</div></div><div class="tile"><span class="label">持仓数</span><div class="metric">13</div></div><div class="tile"><span class="label">年化</span><div class="metric up">12.6%</div></div></div><div class="table"><div class="row"><b>代码</b><b>权重</b><b>盈亏</b></div><div class="row"><span>000001</span><span>18%</span><span class="up">+2.1%</span></div><div class="row"><span>002982</span><span>32%</span><span class="down">-0.8%</span></div></div><div class="chart"></div></div></article>
    <article class="concept c7"><div class="concept-head"><div><h2>07 因子研究版</h2><p>面向因子筛选、横截面对比和策略归因，适合后续扩展因子模块。</p></div><span class="badge">可扩展</span></div><div class="mock"><div class="bar"><span>因子研究台</span><span>动量 / 质量 / 估值 / 波动</span></div><div class="side"><b>筛选器</b><p>市场、行业、因子分位、再平衡周期</p></div><div class="chart"></div><div class="table"><div class="row"><b>因子</b><b>IC</b><b>RankIC</b></div><div class="row"><span>Momentum</span><span class="up">0.08</span><span>0.12</span></div></div></div></article>
    <article class="concept c8"><div class="concept-head"><div><h2>08 宏观复盘版</h2><p>适合经济历史、估值周期、宏观事件和资产对比放到一个叙事界面。</p></div><span class="badge">研究报告感</span></div><div class="mock"><div class="bar"><span>宏观与估值周期</span><span>事件时间线</span></div><div class="chart"></div><div class="tile"><span class="label">PE</span><div class="metric">18.4</div></div><div class="tile"><span class="label">利率</span><div class="metric warn">3.8%</div></div></div></article>
    <article class="concept c9"><div class="concept-head"><div><h2>09 AI 复盘助手版</h2><p>突出自然语言 Agent，把用户请求、AI 解释、观察信号和资料依据放到同一个闭环。</p></div><span class="badge">AI 优先</span></div><div class="mock"><div class="bar"><span>AI 复盘助手</span><span class="up">Agent Online</span></div><div class="hero"><div class="panel"><span class="label">你的请求</span><div class="metric">分析 002982</div></div><div class="chart"></div></div><div class="side"><span class="label">综合结论</span><div class="metric up">继续观察</div></div><div class="table"><div class="row"><span>观察信号</span><span>AI</span><span>风控</span></div></div></div></article>
    <article class="concept c10"><div class="concept-head"><div><h2>10 高管简报版</h2><p>最干净，适合看重点结论、组合状态、日报摘要和一键导出。</p></div><span class="badge">最克制</span></div><div class="mock"><div class="bar"><span>投研简报</span><span>今日摘要</span></div><div class="hero"><span class="label">核心判断</span><div class="metric">组合维持中性偏多</div><p>风险可控，关注回撤和流动性变化。</p></div><div class="tile"><span class="label">今日任务</span><div class="metric">4</div></div><div class="table"><div class="row"><b>模块</b><b>状态</b><b>动作</b></div><div class="row"><span>持仓</span><span class="up">正常</span><span>查看</span></div></div></div></article>
  </main>
</body>
</html>
"""


DASHBOARD_PAGE_TEMPLATE = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI 投资复盘助手</title>
  <style>
    :root { --bg:#f5f8fb; --panel:#fff; --ink:#101828; --muted:#667085; --line:#e2e8f0; --brand:#078894; --brand2:#11a7a3; --blue:#2684ff; --purple:#7658e8; --orange:#f28a16; --green:#10a66a; --red:#ef3340; --shadow:0 14px 36px rgba(16,24,40,.07),0 1px 2px rgba(16,24,40,.05); }
    * { box-sizing:border-box; }
    body { margin:0; min-height:100vh; font-family:"Microsoft YaHei","PingFang SC",Arial,sans-serif; color:var(--ink); background:radial-gradient(circle at 85% 0,rgba(7,136,148,.08),transparent 25%),var(--bg); font-size:14px; }
    a { color:inherit; text-decoration:none; }
    .app { min-height:100vh; display:grid; grid-template-columns:252px minmax(0,1fr); }
    .sidebar { position:sticky; top:0; height:100vh; padding:18px; background:rgba(255,255,255,.94); border-right:1px solid var(--line); display:flex; flex-direction:column; gap:18px; }
    .brand { display:flex; align-items:center; gap:14px; padding:0 8px 14px; border-bottom:1px solid var(--line); }
    .brand-mark { width:48px; height:48px; border-radius:12px; display:grid; place-items:center; color:#fff; background:linear-gradient(135deg,var(--brand),var(--brand2)); box-shadow:0 14px 28px rgba(7,136,148,.28); font:900 25px Consolas,monospace; }
    .brand-title { font-size:24px; font-weight:900; }
    .nav { display:grid; gap:8px; }
    .nav a { display:flex; align-items:center; gap:12px; padding:13px 14px; border-radius:10px; color:#263856; font-weight:800; }
    .nav a:hover,.nav a.active { color:#fff; background:linear-gradient(135deg,var(--brand),#0a7184); box-shadow:0 12px 26px rgba(7,136,148,.24); }
    .ico { width:20px; text-align:center; }
    .system-card { margin-top:auto; padding:14px; border:1px solid var(--line); border-radius:12px; background:#fff; box-shadow:0 8px 20px rgba(16,24,40,.04); }
    .system-row { display:flex; justify-content:space-between; gap:8px; padding:8px 0; color:#52637a; font-size:12px; border-bottom:1px solid #eef2f6; }
    .system-row:last-child { border-bottom:0; }
    .dot { width:8px; height:8px; border-radius:999px; background:#16c784; display:inline-block; margin-right:6px; }
    .main { min-width:0; }
    .topbar { min-height:76px; padding:14px 28px; display:flex; justify-content:space-between; align-items:center; gap:18px; background:rgba(255,255,255,.88); border-bottom:1px solid var(--line); backdrop-filter:blur(16px); }
    .market-status { display:flex; align-items:center; gap:18px; padding:10px 16px; border:1px solid var(--line); border-radius:10px; background:#fff; box-shadow:0 8px 18px rgba(16,24,40,.04); color:#40516b; font-size:13px; white-space:nowrap; overflow:auto; }
    .market-status strong { color:var(--green); font-family:Consolas,monospace; }
    .market-status .red { color:var(--red); }
    .search { flex:0 1 280px; display:flex; align-items:center; gap:9px; padding:0 13px; height:42px; border:1px solid var(--line); border-radius:9px; background:#f8fafc; color:#98a2b3; }
    .search input { width:100%; border:0; outline:0; background:transparent; font:inherit; color:var(--ink); }
    .top-actions { display:flex; align-items:center; gap:12px; }
    .icon-btn,.tool-btn,button { display:inline-flex; align-items:center; justify-content:center; border-radius:10px; border:1px solid var(--line); background:#fff; color:#52637a; font-weight:800; }
    .icon-btn { width:36px; height:36px; position:relative; }
    .badge-dot { position:absolute; right:7px; top:5px; width:8px; height:8px; border-radius:999px; background:var(--red); }
    .tool-btn,button { padding:9px 12px; cursor:pointer; }
    .primary { background:linear-gradient(135deg,var(--brand),var(--brand2)); color:#fff; border:0; }
    .user-chip { display:flex; align-items:center; gap:10px; color:#263856; font-weight:900; }
    .avatar { width:34px; height:34px; border-radius:999px; background:#9aa8bd; display:grid; place-items:center; color:#fff; }
    .content { padding:24px 28px 34px; display:grid; gap:18px; }
    .page-head { display:flex; justify-content:space-between; gap:16px; align-items:center; }
    h1 { margin:0; font-size:28px; }
    h2 { margin:0; font-size:16px; }
    .muted { color:var(--muted); line-height:1.6; }
    .panel { background:rgba(255,255,255,.92); border:1px solid var(--line); border-radius:12px; box-shadow:var(--shadow); }
    .panel-head { padding:16px 18px 0; display:flex; justify-content:space-between; gap:12px; align-items:center; }
    .kpi-grid { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:14px; }
    .kpi-card { min-height:150px; padding:20px; background:#fff; border:1px solid var(--line); border-radius:12px; box-shadow:var(--shadow); display:grid; grid-template-columns:minmax(0,1fr) 54px; grid-template-rows:auto auto 1fr; gap:10px 14px; align-items:end; overflow:hidden; }
    .kpi-card .label { grid-column:1/-1; color:#263856; font-weight:800; align-self:start; }
    .kpi-card strong { grid-column:1/-1; min-width:0; max-width:100%; font-size:clamp(20px,1.55vw,25px); font-family:Consolas,"Microsoft YaHei",monospace; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; letter-spacing:0; line-height:1.2; align-self:center; }
    .kpi-card .summary { min-width:0; align-self:end; display:flex; flex-wrap:wrap; gap:4px 8px; color:#52637a; font-size:13px; line-height:1.45; }
    .delta { color:var(--red); font-size:13px; white-space:nowrap; }
    .delta.ok,.up { color:var(--green); }
    .down { color:var(--red); } .warn { color:var(--orange); }
    .circle-icon { width:54px; height:54px; border-radius:999px; display:grid; place-items:center; color:#fff; font-size:24px; background:linear-gradient(135deg,var(--brand),#5cc4c5); align-self:end; justify-self:end; }
    .circle-icon.green { color:#17a76b; background:#d9f8e6; }
    .circle-icon.blue { background:#dbeafe; color:#1d7dea; }
    .circle-icon.purple { background:#ebe4ff; color:var(--purple); }
    .circle-icon.orange { background:#ffedd5; color:var(--orange); }
    .dashboard-grid { display:grid; grid-template-columns:1.05fr 1.35fr 1.2fr; gap:14px; }
    .watch-table { padding:10px 18px 18px; display:grid; }
    .watch-row { display:grid; grid-template-columns:1.15fr .9fr .85fr 72px; gap:10px; padding:10px 0; align-items:center; border-bottom:1px solid #edf2f7; font-size:13px; }
    .watch-row.head { color:#8090a6; font-weight:800; font-size:12px; }
    .watch-row:last-child { border-bottom:0; }
    .spark { height:24px; border-radius:6px; background:linear-gradient(135deg,transparent 45%,rgba(16,166,106,.22) 46%,transparent 54%),linear-gradient(180deg,transparent 40%,rgba(16,166,106,.85) 42%,transparent 46%); }
    .spark.red { background:linear-gradient(135deg,transparent 45%,rgba(239,51,64,.2) 46%,transparent 54%),linear-gradient(180deg,transparent 52%,rgba(239,51,64,.8) 54%,transparent 58%); }
    .chart-panel { min-height:340px; padding:16px 18px 18px; }
    .tabs { display:flex; gap:6px; flex-wrap:wrap; }
    .tabs span,.tabs button { padding:6px 9px; border-radius:6px; background:#f2f5f8; color:#667085; font-size:12px; font-weight:800; border:1px solid transparent; cursor:pointer; }
    .tabs .active { color:var(--brand); background:#e6f7f6; border:1px solid #9bd7d3; }
    .chart { height:246px; margin-top:14px; position:relative; border-bottom:1px solid #d9e2ec; border-left:1px solid #d9e2ec; overflow:hidden; }
    .chart::before { content:""; position:absolute; inset:0; background:linear-gradient(transparent 48px,#eef2f6 49px),linear-gradient(90deg,transparent 92px,#eef2f6 93px); background-size:100% 49px,93px 100%; }
    .chart svg { position:absolute; inset:0; width:100%; height:100%; }
    .legend { display:flex; gap:16px; color:#667085; font-size:12px; font-weight:800; margin-top:10px; }
    .legend b { color:var(--brand); }
    .donut-wrap { display:grid; grid-template-columns:1fr 170px; gap:18px; align-items:center; padding:18px; }
    .donut { width:220px; aspect-ratio:1; border-radius:999px; background:conic-gradient(#04979d 0 62%,#248bf2 62% 80%,#4cc5d7 80% 89%,#f5b52e 89% 96%,#f36b25 96% 98%,#ef4e5a 98% 100%); display:grid; place-items:center; margin:auto; }
    .donut-center { width:112px; aspect-ratio:1; border-radius:999px; background:#fff; display:grid; place-items:center; text-align:center; color:#263856; font-weight:900; box-shadow:inset 0 0 0 1px #e6edf3; }
    .alloc-list { display:grid; gap:14px; font-size:14px; }
    .alloc-item { display:grid; grid-template-columns:12px 1fr auto; gap:10px; align-items:center; color:#52637a; }
    .swatch { width:10px; height:10px; border-radius:999px; background:#04979d; }
    .lower-grid { display:grid; grid-template-columns:1.35fr 1.05fr .85fr; gap:14px; }
    .quick-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; padding:18px; }
    .quick-card { min-height:172px; padding:18px 12px; border-radius:12px; display:grid; justify-items:center; text-align:center; gap:8px; border:1px solid var(--line); }
    .quick-card b { font-size:18px; }
    .quick-card p { margin:0; color:#6b7b91; line-height:1.55; font-size:13px; }
    .quick-card .big { font-size:42px; }
    .quick-card.teal { background:#effafa; color:var(--brand); }
    .quick-card.orange { background:#fff8ed; color:var(--orange); }
    .quick-card.blue { background:#f0f7ff; color:var(--blue); }
    .quick-card.purple { background:#f6f2ff; color:var(--purple); }
    .analysis-list { padding:10px 18px 18px; display:grid; }
    .analysis-row { display:grid; grid-template-columns:1fr auto auto; gap:12px; padding:10px 0; border-bottom:1px solid #edf2f7; align-items:center; font-size:13px; }
    .analysis-row:last-child { border-bottom:0; }
    .tag { padding:4px 8px; border-radius:6px; background:#eaf4ff; color:#1d7dea; font-size:12px; font-weight:800; }
    .tag.green { background:#e8f8ef; color:var(--green); }
    .tag.purple { background:#f0eaff; color:var(--purple); }
    .risk { padding:18px; display:grid; gap:14px; }
    .risk-top { display:flex; align-items:center; gap:12px; }
    .shield { width:42px; height:42px; border-radius:12px; background:linear-gradient(135deg,#0dbb8b,#0a987f); color:#fff; display:grid; place-items:center; font-size:24px; }
    .bar-track { height:7px; border-radius:999px; background:#e8eef5; overflow:hidden; }
    .bar-fill { width:32%; height:100%; background:linear-gradient(90deg,#10b981,#0dbb8b); }
    .risk-row { display:grid; grid-template-columns:1fr auto auto; color:#52637a; font-size:13px; gap:8px; }
    .submit-overlay { position:fixed; inset:0; display:none; place-items:center; background:rgba(20,33,61,.22); z-index:20; }
    .submit-overlay.active { display:grid; }
    .submit-card { width:min(360px,calc(100vw - 32px)); padding:22px; border-radius:12px; background:#fff; text-align:center; border:1px solid var(--line); }
    .spinner { width:36px; height:36px; margin:0 auto 14px; border-radius:999px; border:4px solid rgba(7,136,148,.16); border-top-color:var(--brand); animation:spin .8s linear infinite; }
    @keyframes spin { to { transform:rotate(360deg); } }
    @media (max-width:1280px) { .app { grid-template-columns:1fr; } .sidebar { position:static; height:auto; } .nav { grid-template-columns:repeat(4,1fr); } .dashboard-grid,.lower-grid,.kpi-grid { grid-template-columns:1fr; } .topbar { height:auto; flex-wrap:wrap; padding:14px; } }
    @media (max-width:720px) { .content { padding:16px; } .quick-grid,.donut-wrap { grid-template-columns:1fr; } .watch-row,.analysis-row { grid-template-columns:1fr; } .market-status { flex-wrap:wrap; } }
  </style>
</head>
<body>
  <div class="submit-overlay" id="submitOverlay"><div class="submit-card"><div class="spinner"></div><strong>正在分析</strong><div class="muted">数据源偶尔会慢一点，完成后会自动显示结果。</div></div></div>
  <div class="app">
    <aside class="sidebar">
      <div class="brand"><span class="brand-mark">R</span><span class="brand-title">投资复盘助手</span></div>
      <nav class="nav">
        <a class="active" href="{{ url_for('index') }}"><span class="ico">▥</span>资产总览</a><a href="{{ url_for('analysis_page') }}"><span class="ico">⌁</span>分析台</a><a href="{{ url_for('backtest_compare') }}"><span class="ico">⌘</span>策略研究</a><a href="{{ url_for('economic_history') }}"><span class="ico">⌇</span>经济历史</a><a href="{{ url_for('portfolio_page') }}"><span class="ico">▣</span>组合管理</a><a href="{{ url_for('alerts_page') }}"><span class="ico">◇</span>价格预警</a><a href="{{ url_for('automation_page') }}"><span class="ico">▧</span>自动化任务</a><a href="{{ url_for('analysis_history_page') }}"><span class="ico">◷</span>历史复盘</a><a href="{{ url_for('market_report') }}"><span class="ico">▤</span>市场报告</a><a href="{{ url_for('research_report_page') }}"><span class="ico">▦</span>标准报告</a><a href="{{ url_for('ui_concepts') }}"><span class="ico">⚙</span>界面候选</a>
      </nav>
      <div class="system-card"><div class="system-row"><span>系统状态</span><span><i class="dot"></i>正常运行</span></div><div class="system-row"><span>数据更新</span><span>15:00:04</span></div></div>
    </aside>
    <main class="main">
      <header class="topbar">
        <div class="market-status"><span>市场状态 <i class="dot"></i>已收盘</span><span>05-07 15:00:00</span><span>上证指数 <strong>3,147.74 +0.48%</strong></span><span>深证成指 <strong class="red">9,678.16 -0.23%</strong></span><span>创业板指 <strong class="red">1,881.21 -0.35%</strong></span></div>
        <form class="search" method="post"><span>⌕</span><input name="symbol" placeholder="搜索标的 / 策略 / 报告"><input type="hidden" name="mode" value="analyze"><input type="hidden" name="market" value="{{ default_market }}"><input type="hidden" name="period" value="max"><input type="hidden" name="use_ai" value="false"></form>
        <div class="top-actions"><a class="icon-btn" href="{{ url_for('alerts_page') }}" title="价格预警">♧<i class="badge-dot"></i></a><a class="icon-btn" href="{{ url_for('automation_page') }}" title="自动化设置">⚙</a>{% if current_user %}<span class="user-chip"><span class="avatar">●</span>{{ current_user }} <small class="muted">专业版</small></span><form method="post" action="{{ url_for('logout') }}"><button type="submit">退出</button></form>{% else %}<a class="tool-btn" href="{{ url_for('login') }}">登录</a><a class="tool-btn primary" href="{{ url_for('register') }}">注册</a>{% endif %}</div>
      </header>
      <section class="content">
        <div class="page-head"><h1>资产总览</h1><div><a class="tool-btn" href="{{ url_for('ui_concepts') }}">自定义看板</a> <a class="tool-btn" href="{{ url_for('index') }}">默认看板</a></div></div>{% if error %}<div class="notice error">{{ error }}</div>{% endif %}{% if note %}<div class="notice">{{ note }}</div>{% endif %}
        <section class="kpi-grid"><div class="kpi-card"><div class="label">组合总资产</div><strong>¥ 1,276,842.36</strong><div class="summary"><span>较昨日</span><span class="delta">+12,842.36</span><span class="delta">+1.02%</span></div><div class="circle-icon">▣</div></div><div class="kpi-card"><div class="label">累计收益</div><strong>+127,642.36</strong><div class="summary"><span>累计收益率</span><span class="delta">+11.12%</span></div><div class="circle-icon green">↗</div></div><div class="kpi-card"><div class="label">今日收益</div><strong>+8,712.54</strong><div class="summary"><span>今日收益率</span><span class="delta">+0.69%</span></div><div class="circle-icon blue">¥</div></div><div class="kpi-card"><div class="label">持仓数量</div><strong>{{ holdings|length }}</strong><div class="summary"><span>较昨日</span><span>0</span><span>0.00%</span></div><div class="circle-icon purple">◆</div></div><div class="kpi-card"><div class="label">可用资金</div><strong>¥ 186,542.12</strong><div class="summary"><span>可用保证金</span><span>74.58%</span></div><div class="circle-icon orange">▰</div></div></section>
        <section class="dashboard-grid">
          <div class="panel"><div class="panel-head"><h2>关注标的</h2></div><div class="watch-table"><div class="watch-row head"><span>代码</span><span>名称</span><span>最新价</span><span>走势</span></div>{% if holdings %}{% for h in holdings[:5] %}<div class="watch-row"><span>{{ h.symbol }}</span><span>{{ h.market }}</span><span>{{ "%.4f"|format(h.avg_cost) }}</span><span class="spark"></span></div>{% endfor %}{% else %}<div class="watch-row"><span>000001.SZ</span><span>平安银行</span><span>11.28</span><span class="spark"></span></div><div class="watch-row"><span>600519.SH</span><span>贵州茅台</span><span>1,678.50</span><span class="spark red"></span></div><div class="watch-row"><span>300750.SZ</span><span>宁德时代</span><span>197.55</span><span class="spark"></span></div><div class="watch-row"><span>NVDA.US</span><span>NVIDIA</span><span>894.81</span><span class="spark"></span></div><div class="watch-row"><span>BTC-USD</span><span>比特币</span><span>63,842.10</span><span class="spark"></span></div>{% endif %}<a class="tool-btn" href="{{ url_for('portfolio_page') }}" style="justify-content:center;margin-top:8px;">+ 添加标的</a></div></div>
          <div class="panel chart-panel"><div class="panel-head"><div><h2>组合收益</h2><div class="legend"><span>● 组合收益率 <b id="portfolioReturn">+11.12%</b></span><span>● 沪深300 <b id="benchmarkReturn" style="color:#2684ff;">+2.31%</b></span></div></div><div class="tabs" data-chart-tabs><button type="button" data-range="近一周">近一周</button><button type="button" data-range="近一月">近一月</button><button type="button" data-range="近三月">近三月</button><button type="button" data-range="今年以来" class="active">今年以来</button><button type="button" data-range="近一年">近一年</button><button type="button" data-range="全部">全部</button></div></div><div class="chart"><svg id="dashboardEquityChart" viewBox="0 0 600 240" preserveAspectRatio="none"><path d="M20,160 C75,150 90,110 140,130 S215,85 260,100 S345,72 395,48 S480,42 520,70 S560,88 585,76" fill="none" stroke="#0aa3a3" stroke-width="4"/><path d="M20,170 C90,205 100,160 145,185 S240,160 285,178 S380,170 430,145 S515,155 585,138" fill="none" stroke="#2684ff" stroke-width="3"/></svg></div></div>
          <div class="panel"><div class="panel-head"><h2>资产配置</h2></div><div class="donut-wrap"><div class="donut"><div class="donut-center"><small>总资产</small><br>¥1,276,842</div></div><div class="alloc-list"><div class="alloc-item"><i class="swatch"></i><span>股票</span><b>62.45%</b></div><div class="alloc-item"><i class="swatch" style="background:#248bf2"></i><span>基金</span><b>18.32%</b></div><div class="alloc-item"><i class="swatch" style="background:#4cc5d7"></i><span>债券</span><b>8.76%</b></div><div class="alloc-item"><i class="swatch" style="background:#f5b52e"></i><span>现金</span><b>7.21%</b></div><div class="alloc-item"><i class="swatch" style="background:#f36b25"></i><span>商品</span><b>2.13%</b></div><div class="alloc-item"><i class="swatch" style="background:#ef4e5a"></i><span>其他</span><b>1.13%</b></div></div></div></div>
        </section>
        <section class="lower-grid">
          <div class="panel"><div class="panel-head"><h2>快捷入口</h2></div><div class="quick-grid"><a class="quick-card blue" href="{{ url_for('research_report_page') }}"><span class="big">▦</span><b>投资复盘报告</b><p>上传持仓、净值或交易记录，生成风险复盘</p><span class="tool-btn">生成报告 →</span></a><a class="quick-card teal" href="{{ url_for('portfolio_page') }}"><span class="big">▣</span><b>持仓体检</b><p>查看持仓、集中度、成本和导出持仓记录</p><span class="tool-btn">进入持仓 →</span></a><a class="quick-card orange" href="{{ url_for('alerts_page') }}"><span class="big">◔</span><b>风险预警</b><p>设置价格提醒，跟踪触发状态</p><span class="tool-btn">进入预警 →</span></a><a class="quick-card purple" href="{{ url_for('analysis_history_page') }}"><span class="big">◷</span><b>历史复盘</b><p>查看历史分析记录与图表</p><span class="tool-btn">进入复盘 →</span></a></div></div>
          <div class="panel"><div class="panel-head"><h2>最近分析</h2></div><div class="analysis-list">{% if analysis_history %}{% for item in analysis_history[:5] %}<div class="analysis-row"><span><b>{{ item.symbol }}</b> · {{ item.period or "历史" }}</span><span class="tag {% if item.use_ai %}purple{% else %}green{% endif %}">{{ "深度分析" if item.use_ai else "技术分析" }}</span><a class="tool-btn" href="{{ item.analysis_image or url_for('analysis_history_page') }}">查看</a></div>{% endfor %}{% else %}<div class="analysis-row"><span>还没有分析记录</span><span class="tag">空状态</span><a class="tool-btn" href="{{ url_for('analysis_page') }}">开始分析</a></div>{% endif %}<a class="tool-btn" style="justify-content:center;margin-top:10px;" href="{{ url_for('analysis_history_page') }}">查看全部历史记录 →</a></div></div>
          <div class="panel"><div class="risk"><div class="risk-top"><div class="shield">✓</div><div><b>风险状态　<span class="up">正常</span></b><div class="muted">风险评分</div></div></div><div><div style="display:flex;justify-content:space-between;"><span>32/100</span><b class="up">低</b></div><div class="bar-track"><div class="bar-fill"></div></div></div><div class="risk-row"><span>市场风险</span><b>25</b><b class="up">低</b></div><div class="risk-row"><span>流动性风险</span><b>30</b><b class="up">低</b></div><div class="risk-row"><span>信用风险</span><b>20</b><b class="up">低</b></div><div class="risk-row"><span>集中度风险</span><b>45</b><b class="warn">中</b></div><div class="risk-row"><span>回撤风险</span><b>20</b><b class="up">低</b></div><div class="muted">更新时间：05-07 15:00</div></div></div>
        </section>
      </section>
    </main>
  </div>
  <script>
    document.querySelectorAll('form').forEach(form => form.addEventListener('submit', () => { const mode = form.querySelector('[name="mode"]')?.value || ''; if (['analyze','chat'].includes(mode)) document.getElementById('submitOverlay')?.classList.add('active'); }));
    document.querySelectorAll('[data-chart-tabs] button').forEach(button => button.addEventListener('click', async () => {
      document.querySelectorAll('[data-chart-tabs] button').forEach(item => item.classList.toggle('active', item === button));
      const range = button.dataset.range || button.textContent.trim();
      const chart = document.getElementById('dashboardEquityChart');
      const portfolioReturn = document.getElementById('portfolioReturn');
      const benchmarkReturn = document.getElementById('benchmarkReturn');
      try {
        const preset = await fetch(`/api/ui/dashboard_returns?range=${encodeURIComponent(range)}`).then(r => r.json());
        if (!preset.ok) throw new Error(preset.error || '收益区间读取失败。');
        if (portfolioReturn) portfolioReturn.textContent = preset.portfolio_return;
        if (benchmarkReturn) benchmarkReturn.textContent = preset.benchmark_return;
        if (chart) chart.innerHTML = `<path d="${preset.portfolio_path}" fill="none" stroke="#0aa3a3" stroke-width="4"/><path d="${preset.benchmark_path}" fill="none" stroke="#2684ff" stroke-width="3"/>`;
      } catch (err) {
        button.title = err.message || '收益区间读取失败。';
      }
    }));
  </script>
</body>
</html>
"""


RESEARCH_REPORT_PAGE_TEMPLATE = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>投资复盘报告 - AI 投资复盘助手</title>
  <style>
    :root { --bg:#f5f8fb; --panel:#fff; --ink:#101828; --muted:#667085; --line:#e2e8f0; --brand:#078894; --brand2:#11a7a3; --red:#ef3340; --shadow:0 12px 28px rgba(16,24,40,.07); }
    * { box-sizing:border-box; }
    body { margin:0; min-height:100vh; font-family:"Microsoft YaHei","PingFang SC",Arial,sans-serif; color:var(--ink); background:var(--bg); font-size:14px; }
    a { color:inherit; text-decoration:none; }
    .app { min-height:100vh; display:grid; grid-template-columns:252px minmax(0,1fr); }
    .sidebar { position:sticky; top:0; height:100vh; padding:18px; background:#fff; border-right:1px solid var(--line); display:flex; flex-direction:column; gap:18px; }
    .brand { display:flex; align-items:center; gap:12px; padding-bottom:14px; border-bottom:1px solid var(--line); font-weight:900; font-size:20px; }
    .brand-mark { width:42px; height:42px; border-radius:10px; display:grid; place-items:center; color:#fff; background:linear-gradient(135deg,var(--brand),var(--brand2)); font:900 22px Consolas,monospace; }
    .nav { display:grid; gap:8px; }
    .nav a { display:flex; gap:10px; padding:12px; border-radius:8px; color:#263856; font-weight:800; }
    .nav a.active,.nav a:hover { color:#fff; background:linear-gradient(135deg,var(--brand),#0a7184); }
    .main { min-width:0; }
    .topbar { min-height:70px; padding:14px 28px; display:flex; justify-content:space-between; align-items:center; gap:18px; background:#fff; border-bottom:1px solid var(--line); }
    .content { padding:24px 28px 34px; display:grid; gap:18px; }
    .page-head { display:flex; justify-content:space-between; gap:16px; align-items:flex-start; }
    h1 { margin:0; font-size:30px; letter-spacing:0; }
    h2 { margin:0; font-size:17px; }
    p,.muted { color:var(--muted); line-height:1.65; margin:0; }
    .panel { background:var(--panel); border:1px solid var(--line); border-radius:10px; box-shadow:var(--shadow); }
    .panel-pad { padding:18px; }
    .report-grid { display:grid; grid-template-columns:380px minmax(0,1fr); gap:14px; align-items:start; }
    .form-panel { display:grid; gap:14px; }
    label { display:grid; gap:7px; color:#263856; font-weight:800; }
    input,select,textarea { width:100%; min-height:42px; padding:9px 10px; border-radius:8px; border:1px solid #cfd7df; background:#fff; font:inherit; color:var(--ink); }
    textarea { min-height:106px; resize:vertical; }
    button,.btn { display:inline-flex; align-items:center; justify-content:center; border-radius:8px; border:1px solid var(--line); background:#fff; color:#52637a; font-weight:800; padding:9px 12px; cursor:pointer; font:inherit; }
    .primary { background:linear-gradient(135deg,var(--brand),var(--brand2)); color:#fff; border:0; }
    .actions { display:flex; gap:8px; flex-wrap:wrap; align-items:center; }
    .notice { padding:11px 13px; border-radius:8px; background:#e6f7f6; border:1px solid #9bd7d3; color:#0f6f82; font-weight:800; }
    .notice.error { background:#fff1f0; border-color:#ffd2cc; color:var(--red); }
    .reader-head { padding:18px 18px 0; display:flex; justify-content:space-between; gap:12px; align-items:flex-start; flex-wrap:wrap; }
    .report { margin:16px 18px 18px; white-space:pre-wrap; background:#fff; color:#1f2937; border:1px solid var(--line); border-left:4px solid var(--brand); border-radius:8px; padding:16px; line-height:1.78; overflow:auto; max-height:720px; font-family:Consolas,"Microsoft YaHei",monospace; font-size:13px; }
    .hint { padding:12px; border:1px solid var(--line); border-radius:8px; background:#f8fafc; color:#475467; line-height:1.7; }
    .followup-panel { margin:16px 18px 0; padding:14px; border:1px solid #bfdbfe; border-radius:8px; background:#eff6ff; display:grid; gap:10px; }
    .followup-output { display:grid; gap:8px; max-height:260px; overflow:auto; }
    .followup-message { padding:10px 12px; border:1px solid var(--line); border-radius:8px; background:#fff; color:#344054; line-height:1.65; white-space:pre-wrap; }
    .followup-message.user { background:#f8fafc; font-weight:800; }
    .history-list { display:grid; gap:10px; padding:10px 18px 18px; }
    .history-item { display:grid; grid-template-columns:minmax(0,1fr) auto; gap:12px; align-items:center; padding:12px 0; border-bottom:1px solid #edf2f7; }
    .empty { padding:32px 18px; color:var(--muted); }
    @media (max-width:1000px) { .app { grid-template-columns:1fr; } .sidebar { position:static; height:auto; } .report-grid { grid-template-columns:1fr; } }
  </style>
</head>
<body>
  <div class="app">
    <aside class="sidebar">
      <div class="brand"><span class="brand-mark">R</span><span>投资复盘助手</span></div>
      <nav class="nav">
        <a href="{{ url_for('index') }}">资产总览</a>
        <a href="{{ url_for('analysis_page') }}">分析台</a>
        <a href="{{ url_for('portfolio_page') }}">组合管理</a>
        <a href="{{ url_for('market_report') }}">市场报告</a>
        <a class="active" href="{{ url_for('research_report_page') }}">复盘报告</a>
      </nav>
      <div class="hint">上传持仓、净值或交易记录，生成可追溯的投资复盘与风险报告，并标注资料来源与引用。</div>
    </aside>
    <main class="main">
      <header class="topbar">
        <strong>投资复盘报告</strong>
        <div class="actions"><a class="btn" href="{{ url_for('analysis_page') }}">去分析台</a><a class="btn" href="{{ url_for('index') }}">返回控制台</a></div>
      </header>
      <section class="content">
        <div class="page-head">
          <div><h1>投资复盘与风险报告</h1><p>上传持仓、净值或交易记录，生成过去表现、风险解释、集中度检查和下一步观察清单。</p></div>
          <div class="actions"><a class="btn" href="{{ url_for('download_research_template') }}">下载 CSV 数据模板</a></div>
        </div>
        {% if error %}<div class="notice error">{{ error }}</div>{% endif %}
        {% if note %}<div class="notice">{{ note }}</div>{% endif %}
        <section class="report-grid">
          <div class="panel panel-pad form-panel">
            <h2>上传数据生成复盘报告</h2>
            <form method="post" enctype="multipart/form-data">
              <label>报告类型
                <select name="report_type">
                  {% for item in ['个人持仓体检报告','基金/ETF 分析报告','小资金组合风险报告','交易复盘报告','亏损原因分析报告','定投/补仓观察报告','每周账户复盘报告'] %}<option value="{{ item }}">{{ item }}</option>{% endfor %}
                </select>
              </label>
              <label>读者版本
                <select name="audience">
                  {% for item in ['个人投资者版','小资金账户版','业余量化版','小型投研团队版'] %}<option value="{{ item }}">{{ item }}</option>{% endfor %}
                </select>
              </label>
              <label>数据广度
                <select name="data_breadth">
                  <option value="标准" selected>标准：用户数据 + 行情数据 + 基础资料</option>
                  <option value="基础">基础：只用用户上传数据</option>
                  <option value="深度">深度：标准资料 + 新闻/公告/市场背景</option>
                </select>
              </label>
              <label>本次报告要解决什么问题
                <textarea name="objective" placeholder="例如：看这只基金最近是否变差；复核组合是否过于集中；分析最近亏损可能来自哪里。"></textarea>
              </label>
              <label>数据文件 <input type="file" name="data_file" accept=".csv,.xlsx,.xls" required></label>
              <button class="primary" type="submit">生成投资复盘报告</button>
            </form>
            <form method="post" action="{{ url_for('create_sample_research_report') }}">
              <input type="hidden" name="report_type" value="基金/ETF 分析报告">
              <input type="hidden" name="audience" value="个人投资者版">
              <input type="hidden" name="data_breadth" value="标准">
              <input type="hidden" name="objective" value="使用示例净值曲线演示投资复盘报告工作流。">
              <button type="submit">没有数据，先生成示例报告</button>
            </form>
            <div class="hint">最低可用字段：date + nav/close/return。持仓体检建议补充 symbol、quantity、avg_cost、weight；交易复盘建议补充 pnl、买入日期、卖出日期和手续费。</div>
          </div>
          <div class="panel">
            {% if latest %}
            <div class="reader-head">
              <div><h2>{{ latest.title }}</h2><p>{{ latest.generated_at }}</p></div>
              <div class="actions">
                <a class="btn primary" href="{{ url_for('download_research_report', report_id=latest.id, fmt='md') }}">Markdown</a>
                <a class="btn primary" href="{{ url_for('download_research_report', report_id=latest.id, fmt='pdf') }}">PDF</a>
                <a class="btn primary" href="{{ url_for('download_research_report', report_id=latest.id, fmt='docx') }}">Word</a>
              </div>
            </div>
            <div class="followup-panel" data-followup-card data-report-id="{{ latest.id }}">
              <strong>继续追问报告</strong>
              <textarea class="followup-question" placeholder="例如：这份数据能不能用？最大风险是什么？如果继续跌，我该观察什么？"></textarea>
              <div class="actions"><button type="button" class="primary followup-send">发送追问</button></div>
              <div class="followup-output"></div>
            </div>
            <div class="report" data-followup-context>{{ latest.markdown }}</div>
            {% else %}
            <div class="empty"><h2>暂无报告</h2><p>上传持仓、净值或交易记录后，这里会显示复盘结论、风险解释和下一步观察清单。</p></div>
            {% endif %}
          </div>
        </section>
        <section class="panel">
          <div class="reader-head"><h2>历史复盘报告</h2></div>
          {% if reports %}
          <div class="history-list">
            {% for report in reports %}
            <article class="history-item">
              <div><strong>{{ report.title }} · {{ report.generated_at }}</strong><p>{{ report.subject if report.subject else report.id }}</p></div>
              <div class="actions">
                <a class="btn" href="{{ url_for('download_research_report', report_id=report.id, fmt='md') }}">Markdown</a>
                <a class="btn" href="{{ url_for('download_research_report', report_id=report.id, fmt='pdf') }}">PDF</a>
                <a class="btn" href="{{ url_for('download_research_report', report_id=report.id, fmt='docx') }}">Word</a>
              </div>
            </article>
            {% endfor %}
          </div>
          {% else %}<div class="empty">暂无历史报告。</div>{% endif %}
        </section>
      </section>
    </main>
  </div>
  <script>
    function appendFollowupMessage(box, text, cls) {
      const node = document.createElement('div');
      node.className = `followup-message ${cls || ''}`.trim();
      node.textContent = text;
      box.appendChild(node);
      box.scrollTop = box.scrollHeight;
    }
    document.querySelectorAll('[data-followup-card]').forEach(card => {
      const output = card.querySelector('.followup-output');
      const textarea = card.querySelector('.followup-question');
      const contextNode = document.querySelector('[data-followup-context]');
      card.querySelector('.followup-send')?.addEventListener('click', async () => {
        const question = (textarea?.value || '').trim();
        if (!question) return;
        appendFollowupMessage(output, question, 'user');
        textarea.value = '';
        appendFollowupMessage(output, 'Agent 正在分析...', '');
        const waitingNode = output.lastElementChild;
        const formData = new FormData();
        formData.append('csrf_token', '{{ csrf_token() }}');
        formData.append('question', question);
        formData.append('report_id', card.dataset.reportId || '');
        formData.append('context', contextNode?.textContent || '');
        try {
          const res = await fetch('{{ url_for("report_followup_api") }}', { method:'POST', body:formData });
          const data = await res.json();
          waitingNode.textContent = data.ok ? data.answer : (data.error || '追问失败，请稍后重试。');
        } catch (err) {
          waitingNode.textContent = '追问失败，请检查 API 配置或稍后重试。';
        }
      });
    });
  </script>
</body>
</html>
"""

