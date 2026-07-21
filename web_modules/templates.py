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
    body { margin:0; min-height:100vh; overflow:hidden; color:var(--ink); background:var(--bg); font:14px/1.45 "Microsoft YaHei","PingFang SC",Arial,sans-serif; }
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
    .shell { max-width:none; padding:0; }
    .layout { height:calc(100vh - 52px); min-height:0; display:grid; grid-template-columns:260px minmax(0,1fr) 300px; overflow:hidden; }
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
    .left-rail { grid-column:1; min-width:0; height:100%; padding:16px 18px 82px; border-right:1px solid var(--line); background:#fff; overflow:auto; scrollbar-gutter:stable; }
    .report-main { grid-column:2; min-width:0; height:100%; padding:16px 18px 82px; background:#fff; overflow:auto; border-right:1px solid var(--line); scrollbar-gutter:stable; }
    .right-rail { grid-column:3; min-width:0; height:100%; padding:16px 18px 82px; background:#fff; overflow:auto; scrollbar-gutter:stable; }
    #agent-panel,#direct-panel { padding:0; }
    #agent-panel { margin-top:18px; display:none; }
    .result-panel { padding:0; background:#fff; color:var(--ink); }
    .result-panel .muted { color:var(--muted); }
    .result-panel .chip { color:#344054; background:#fff; border-color:var(--line); }
    .section-title { display:flex; align-items:center; gap:8px; margin:12px 0 8px; font-weight:900; }
    .section-title::before { content:""; width:3px; height:18px; background:var(--brand); border-radius:2px; }
    .summary-box { padding:0; border:0; border-radius:0; background:#fff; }
    .summary-box strong { display:block; margin-bottom:5px; font-size:15px; }
    .kpis { display:grid; grid-template-columns:repeat(6,minmax(84px,1fr)); border:1px solid var(--line); border-radius:5px; overflow:hidden; margin-bottom:12px; }
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
    .reader-note,.action-feedback { margin-top:8px; padding:8px 10px; border:1px solid var(--line); border-radius:6px; background:#f8fafc; color:#344054; line-height:1.5; }
    .action-feedback input { width:100%; margin-top:6px; font:12px/1.4 Consolas,"Microsoft YaHei",monospace; }
    .image-grid { display:grid; gap:14px; margin-top:14px; }
    .image-card { border:1px solid var(--line); border-radius:6px; overflow:hidden; background:#fff; }
    .image-card img { width:100%; min-height:320px; object-fit:contain; display:block; background:#f8fafc; }
    .image-card div { padding:9px 12px; color:#475467; font-size:12px; font-weight:800; border-top:1px solid var(--line); }
    .assumption-list,.export-list,.check-list { display:grid; gap:0; border:0; border-radius:0; overflow:hidden; background:#fff; }
    .assumption-list div,.check-list div { display:grid; grid-template-columns:1fr auto; gap:10px; padding:9px 0; border-bottom:1px solid var(--line-2); font-size:13px; }
    .assumption-list div:last-child,.check-list div:last-child { border-bottom:0; }
    .assumption-list b,.check-list b { font-weight:800; color:#344054; }
    .side-details { margin-top:18px; border-top:1px solid var(--line-2); border-bottom:1px solid var(--line-2); }
    .side-details summary { min-height:42px; display:flex; align-items:center; justify-content:space-between; gap:10px; list-style:none; cursor:pointer; font-weight:900; }
    .side-details summary::-webkit-details-marker { display:none; }
    .side-details summary::after { content:"+"; width:22px; height:22px; border:1px solid var(--line); border-radius:5px; display:grid; place-items:center; color:#475467; font:900 15px/1 Consolas,monospace; background:#fff; }
    .side-details[open] summary::after { content:"-"; }
    .side-details-body { padding:0 0 8px; }
    .side-details-body .muted { margin-bottom:6px; }
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
    .workflow { position:fixed; left:0; right:0; bottom:0; z-index:5; display:grid; grid-template-columns:220px minmax(0,1fr) 220px; align-items:center; gap:16px; min-height:56px; padding:9px 18px; border-top:1px solid var(--line); background:rgba(255,255,255,.98); box-shadow:0 -4px 14px rgba(16,24,40,.04); }
    .workflow-title { min-width:0; font-weight:900; }
    .workflow-title::before { content:""; display:inline-block; width:3px; height:18px; background:var(--brand); border-radius:2px; margin-right:8px; vertical-align:-4px; }
    .log-stream { min-width:0; display:flex; align-items:center; gap:12px; overflow:hidden; color:#475467; white-space:nowrap; }
    .log-item { min-width:0; display:inline-flex; align-items:center; gap:5px; }
    .log-item time,.log-row time { color:#667085; font-family:Consolas,"Microsoft YaHei",monospace; font-size:12px; }
    .log-item span { overflow:hidden; text-overflow:ellipsis; }
    .workflow-status { min-width:0; display:flex; align-items:center; justify-content:flex-end; gap:10px; color:#475467; font-size:12px; white-space:nowrap; }
    .workflow-status .dot-ok { margin-left:0; margin-right:4px; }
    .workflow-log-details { position:relative; }
    .workflow-log-details summary { list-style:none; }
    .workflow-log-details summary::-webkit-details-marker { display:none; }
    .workflow-log-panel { position:absolute; right:0; bottom:40px; width:min(460px,calc(100vw - 36px)); display:grid; gap:0; padding:8px 12px; border:1px solid var(--line); border-radius:6px; background:#fff; box-shadow:0 12px 32px rgba(15,23,42,.14); white-space:normal; }
    .log-row { display:grid; grid-template-columns:58px 1fr; gap:10px; padding:7px 0; border-bottom:1px solid var(--line-2); color:#344054; }
    .log-row:last-child { border-bottom:0; }
    .submit-overlay { position:fixed; inset:0; display:none; place-items:center; background:rgba(16,24,40,.18); z-index:20; }
    .submit-overlay.active { display:grid; }
    .submit-card { width:min(360px,calc(100vw - 32px)); padding:22px; border-radius:8px; background:#fff; text-align:center; border:1px solid var(--line); box-shadow:var(--shadow); }
    .submit-card small { display:block; margin-top:8px; color:#667085; font-size:12px; line-height:1.5; }
    .spinner { width:34px; height:34px; margin:0 auto 14px; border-radius:999px; border:4px solid rgba(37,99,235,.14); border-top-color:var(--brand); animation:spin .8s linear infinite; }
    @keyframes spin { to { transform:rotate(360deg); } }
    @media (max-width:1180px) { .layout { grid-template-columns:240px minmax(0,1fr) 280px; } .left-rail,.report-main,.right-rail { padding:14px 14px 78px; } .report-grid-2 { grid-template-columns:1fr; } .workflow { grid-template-columns:170px minmax(0,1fr) 190px; gap:10px; padding-left:14px; padding-right:14px; } .workflow-title { font-size:13px; } .workflow-status { font-size:11px; } }
    @media (max-width:900px) { body { overflow:auto; } .top-nav { height:auto; min-height:56px; grid-template-columns:1fr; gap:8px; padding:10px 14px; } .report-title { text-align:left; } .nav-actions { justify-self:start; flex-wrap:wrap; } .layout { display:flex; flex-direction:column; height:auto; min-height:calc(100vh - 56px); overflow:visible; } .report-main { order:1; } .left-rail { order:2; } .right-rail { order:3; } .left-rail,.report-main,.right-rail { height:auto; border:0; padding:14px; overflow:visible; } .report-main,.right-rail { border-top:1px solid var(--line); } .kpis,.row-2,.reader-main .reader-switch { grid-template-columns:1fr; } .kpi { border-right:0; border-bottom:1px solid var(--line); } .workflow { order:4; position:static; grid-template-columns:1fr; align-items:start; gap:8px; min-height:auto; padding:10px 14px; } .workflow-title,.workflow-status,.log-stream { grid-column:1 / -1; justify-content:flex-start; } .workflow-status { flex-wrap:wrap; } .workflow-log-panel { position:static; width:100%; margin-top:8px; } table { min-width:640px; } }
    body.module-analysis { overflow:auto; background:#f6f8fc; }
    .top-nav { display:none; }
    .icon-sprite { position:absolute; width:0; height:0; overflow:hidden; }
    .ui-icon { width:18px; height:18px; display:block; flex:0 0 auto; fill:none; stroke:currentColor; stroke-width:1.8; stroke-linecap:round; stroke-linejoin:round; }
    .app-sidebar { position:fixed; inset:0 auto 0 0; z-index:6; width:188px; padding:24px 20px; background:#fff; border-right:1px solid #eef2f7; display:flex; flex-direction:column; gap:26px; }
    .side-nav { display:grid; gap:10px; }
    .side-item { width:100%; min-height:40px; border:0; border-radius:6px; padding:0 13px; display:grid; grid-template-columns:20px 1fr 16px; align-items:center; gap:9px; background:transparent; color:#1f2937; text-align:left; font-size:15px; font-weight:700; text-decoration:none; cursor:pointer; }
    .side-item.active { background:#dff4ff; }
    .side-item .nav-icon { color:#2563eb; }
    .side-chevron,.tool-row-chevron { justify-self:end; width:16px; height:16px; transition:transform .18s ease; }
    .side-tool-group { margin:0; }
    .side-tool-group > summary { list-style:none; }
    .side-tool-group > summary::-webkit-details-marker,.tool-row-group > summary::-webkit-details-marker { display:none; }
    .side-tool-group[open] > summary .side-chevron { transform:rotate(180deg); }
    .side-tool-menu { margin:5px -20px 0; border-top:1px solid #f97316; background:#fff; }
    .tool-row-group { margin:0; border-bottom:1px solid #dde3ea; }
    .tool-row-group > summary { min-height:48px; padding:0 20px; display:grid; grid-template-columns:18px 1fr 16px; align-items:center; gap:10px; list-style:none; color:#43505f; font-size:15px; font-weight:500; cursor:pointer; }
    .tool-row-group > summary:hover { background:#f8fafc; color:#1f2937; }
    .side-item:focus-visible,.tool-row-group > summary:focus-visible { outline:2px solid rgba(37,99,235,.34); outline-offset:-2px; }
    .tool-row-group[open] > summary .tool-row-chevron { transform:rotate(180deg); }
    .tool-row-group .tool-icon { width:17px; height:17px; color:#64748b; }
    .tool-row-body { display:grid; padding:4px 0 7px; border-top:1px solid #eef2f6; background:#fbfcfe; }
    .tool-row-body a { min-height:32px; padding:7px 20px 7px 48px; display:flex; align-items:center; color:#64748b; font-size:13px; font-weight:600; text-decoration:none; }
    .tool-row-body a:hover { background:#eef7ff; color:#2563eb; }
    .side-spacer { flex:1; }
    .app-home { min-height:100vh; margin-left:188px; padding:24px 32px 0; background:#f6f8fc; }
    .search-hero { width:min(720px,100%); margin:0 auto; padding-top:min(16vh,130px); text-align:center; }
    .hero-title { margin:0 0 72px; color:#2f8ff0; font-size:25px; line-height:1.25; font-weight:500; }
    .hero-search { height:52px; display:grid; grid-template-columns:minmax(0,1fr) 56px; align-items:center; border:2px solid transparent; border-radius:6px; background:linear-gradient(#fff,#fff) padding-box, linear-gradient(90deg,#74c7ff,#a566ff,#ff4757) border-box; box-shadow:0 8px 22px rgba(37,99,235,.08); }
    .hero-search input[type="text"] { height:48px; border:0; outline:0; padding:0 18px; background:transparent; font-size:14px; color:#111827; }
    .hero-search input[type="text"]:focus { outline:0; border-color:transparent; }
    .hero-search button { width:56px; min-height:48px; padding:0; border:0; border-radius:0 4px 4px 0; background:transparent; color:#3367d6; display:grid; place-items:center; }
    .hero-submit-icon { width:27px; height:27px; fill:currentColor; stroke:none; transition:transform .15s ease,color .15s ease; }
    .hero-search button:hover .hero-submit-icon { color:#1d4ed8; transform:translateX(2px); }
    .hero-suggestions { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:0; width:min(520px,92%); margin:11px auto 0; color:#6b7280; font-size:11px; }
    .hero-suggestions button { min-height:20px; padding:0 10px; border:0; border-right:1px solid #e5e7eb; border-radius:0; background:transparent; color:#6b7280; font-size:11px; font-weight:500; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .hero-suggestions button:last-child { border-right:0; }
    .shell { margin-left:188px; padding:0 32px 56px; background:#f6f8fc; }
    .shell .layout { width:min(1120px,100%); height:auto; min-height:0; margin:0 auto; display:grid; grid-template-columns:minmax(0,1fr); gap:18px; overflow:visible; }
    .stack { display:none; }
    .report-main,.right-rail { height:auto; padding:0; border:0; background:transparent; overflow:visible; }
    .report-main { grid-column:1; }
    .right-rail { grid-column:1; }
    .result-panel,.right-rail section,.right-rail details,.workflow { border:1px solid var(--line); border-radius:8px; background:#fff; }
    .result-panel { padding:18px; }
    .right-rail section,.right-rail details { padding:14px; margin-top:0 !important; }
    .right-rail section + section,.right-rail details + section,.right-rail section + details { margin-top:14px !important; }
    .workflow { grid-column:1 / -1; position:static; left:auto; right:auto; bottom:auto; z-index:auto; grid-template-columns:140px minmax(0,1fr) 190px; min-height:54px; padding:10px 14px; box-shadow:none; }
    .workflow-log-panel { bottom:38px; }
    @media (max-width:900px) {
      .app-sidebar { position:static; width:auto; height:auto; padding:12px 16px; display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); align-items:center; gap:8px; }
      .side-nav { display:contents; }
      .side-tool-group { display:block; min-width:0; }
      .side-tool-menu { display:none; }
      .side-item { min-width:0; min-height:34px; display:flex; align-items:center; justify-content:center; padding:0 8px; font-size:13px; white-space:nowrap; }
      .side-item .nav-icon,.side-item .side-chevron { display:none; }
      .side-spacer { display:none; }
      .app-home,.shell { margin-left:0; padding-left:16px; padding-right:16px; }
      .app-home { min-height:520px; }
      .search-hero { padding-top:72px; }
      .hero-title { margin-bottom:42px; font-size:22px; }
      .hero-suggestions { grid-template-columns:repeat(2,minmax(0,1fr)); row-gap:6px; }
      .hero-suggestions button { border-right:0; }
      .hero-search { grid-template-columns:minmax(0,1fr) 48px; }
      .hero-search button { width:48px; }
      .shell .layout { display:grid; grid-template-columns:1fr; }
      .report-main,.right-rail,.workflow { grid-column:1; }
      .workflow { grid-template-columns:1fr; }
    }
    :root {
      --page:#f6f8fc;
      --surface:#ffffff;
      --surface-soft:#fbfdff;
      --text:#172033;
      --text-soft:#344054;
      --border:#e7edf5;
      --border-strong:#d9e4f0;
      --accent:#2f7d78;
      --accent-strong:#2f6fcb;
      --accent-soft:#eef8f6;
      --warm:#b7791f;
      --warm-soft:#fff8e8;
      --success-soft:#eefaf4;
      --warning-soft:#fff6df;
      --danger-soft:#fff1ef;
      --radius:8px;
      --radius-lg:8px;
      --card-shadow:0 10px 24px rgba(28,43,64,.055);
    }
    body.module-analysis { color:var(--text); background:var(--page); }
    .app-sidebar,.app-home,.shell { background:var(--page); }
    .app-sidebar { background:#fff; border-right:1px solid #edf2f7; }
    .side-item { color:#2b3648; border-radius:var(--radius); transition:background .15s ease,color .15s ease; }
    .side-item.active,.side-item:hover { background:#e5f5ff; color:#142033; }
    .side-item .nav-icon { color:var(--accent-strong); }
    .hero-title { color:#1f4f4b; font-weight:650; }
    .hero-title::after { content:"先看风险，再看机会；先留证据，再下结论。"; display:block; margin-top:12px; color:#667085; font-size:15px; font-weight:500; }
    .hero-search {
      border:1px solid #b9d8d2;
      border-radius:var(--radius);
      background:#fff;
      box-shadow:0 12px 28px rgba(47,125,120,.10);
    }
    .hero-search:focus-within {
      border-color:#68aaa2;
      box-shadow:0 0 0 4px rgba(47,125,120,.10), 0 12px 28px rgba(47,125,120,.10);
    }
    .hero-search button { border:0; background:transparent; color:#2f6fcb; box-shadow:none; }
    .hero-suggestions button { color:#667085; }
    .result-panel,.right-rail section,.right-rail details,.workflow {
      border:1px solid var(--border);
      border-radius:var(--radius-lg);
      background:var(--surface);
      box-shadow:var(--card-shadow);
    }
    .result-panel { padding:20px; }
    .right-rail section,.right-rail details { padding:16px; }
    .panel-head,.reader-main-head { align-items:center; margin-bottom:12px; }
    .right-rail h2,.section-title { color:var(--text); font-size:15px; font-weight:900; }
    .section-title { margin:16px 0 10px; }
    .section-title::before,.workflow-title::before { width:3px; height:18px; background:var(--accent); }
    .summary-box {
      margin-bottom:14px;
      padding:12px 14px;
      border:1px solid var(--border);
      border-radius:var(--radius);
      background:var(--surface-soft);
    }
    .reader-main,.agent-card {
      border:1px solid #d8ebe8;
      border-radius:var(--radius-lg);
      background:linear-gradient(180deg,#fff 0%,#fbfefd 100%);
    }
    .reader-main { padding:14px; }
    .reader-switch { gap:8px; }
    .chip,.auth-btn,.workflow-log-details summary,.export-list button,.followup-send {
      min-height:34px;
      border-radius:var(--radius);
      border-color:var(--border-strong);
      background:#fff;
      color:var(--text-soft);
      font-size:13px;
      font-weight:800;
      box-shadow:none;
      transition:background .15s ease,border-color .15s ease,color .15s ease;
    }
    .chip:hover,.auth-btn:hover,.workflow-log-details summary:hover,.export-list button:hover {
      border-color:#a9d8d2;
      background:var(--accent-soft);
      color:#1f6862;
    }
    button.primary,.primary,.reader-switch .active,.tabs .active,.export-list .primary {
      border-color:var(--accent-strong);
      background:var(--accent-strong);
      color:#fff;
      box-shadow:0 8px 18px rgba(37,99,235,.12);
    }
    .reader-note,.action-feedback,.followup-message.user {
      border-color:var(--border);
      border-radius:var(--radius);
      background:var(--surface-soft);
      color:#475467;
    }
    .evidence-note {
      margin:10px 0 14px;
      padding:10px 12px;
      border:1px solid #e5d7b7;
      border-left:3px solid var(--warm);
      border-radius:var(--radius);
      background:var(--warm-soft);
      color:#66502a;
      line-height:1.55;
      font-size:13px;
    }
    .search-result-head h2::after {
      content:"观察，不是指令";
      display:inline-flex;
      margin-left:10px;
      padding:3px 7px;
      border:1px solid #cde7df;
      border-radius:999px;
      background:#f3fbf8;
      color:#2f756e;
      font-size:12px;
      font-weight:800;
      vertical-align:4px;
    }
    .history-chart-head h3::after {
      content:"随本次数据重绘";
      margin-left:8px;
      color:#667085;
      font-size:12px;
      font-weight:700;
    }
    .buy-data-table h3::after {
      content:"用于复核，不替你做决定";
      margin-left:8px;
      color:#667085;
      font-size:12px;
      font-weight:700;
    }
    .explain-button {
      min-height:auto;
      padding:0;
      border:0;
      border-radius:0;
      background:transparent;
      color:inherit;
      font:inherit;
      font-weight:800;
      text-decoration:underline dotted rgba(47,143,240,.45);
      text-underline-offset:3px;
    }
    .explain-button:hover { background:transparent; color:var(--accent-strong); }
    .kpis,.metric-table,.mini-chart {
      border-color:var(--border);
      border-radius:var(--radius-lg);
      background:#fff;
    }
    .kpi { padding:14px 12px; border-right:1px solid var(--border); }
    .kpi span { color:#667085; font-size:12px; }
    .kpi strong { color:#111827; font-size:19px; }
    .metric-table th {
      background:#f8fbff;
      color:#4b5b72;
      font-size:12px;
      letter-spacing:0;
    }
    .metric-table td,.metric-table th { border-bottom:1px solid var(--border); }
    .metric-table tbody tr:hover { background:#fbfdff; }
    .mini-chart svg rect { fill:#fff; }
    .bar { background:#edf2f7; }
    .bar i { background:#73b8ad; }
    .heat.pos { background:var(--success-soft); }
    .heat.neg { background:var(--danger-soft); }
    .risk-badge {
      border-radius:var(--radius);
      background:var(--warning-soft);
      color:var(--warn);
    }
    .assumption-list div,.check-list div { border-bottom:1px solid var(--border); }
    .assumption-list b,.check-list b { color:#3a4a60; }
    .side-details { border:1px solid var(--border) !important; }
    .side-details summary { min-height:38px; }
    .side-details summary::after {
      border-color:var(--border-strong);
      border-radius:var(--radius);
      color:#667085;
      background:#fff;
    }
    .risk-details summary .risk-badge { margin-left:auto; min-width:72px; padding:4px 8px; font-size:12px; }
    .risk-details summary::after { margin-left:2px; }
    .agent-card { padding:14px; }
    .agent-card strong { color:var(--text); }
    .notice {
      border-color:#ffd9a8;
      border-radius:var(--radius);
      background:#fff8ed;
      color:#9a3412;
    }
    .error { border-color:#ffd0ca; background:#fff3f1; }
    .workflow {
      margin-top:0;
      color:#475467;
    }
    .workflow-log-panel {
      border-color:var(--border);
      border-radius:var(--radius);
      box-shadow:0 16px 36px rgba(16,24,40,.12);
    }
    .app-sidebar { width:220px; padding:20px 0; gap:0; }
    .sidebar-disclaimer { margin:0 18px 14px; padding:10px 12px; border:1px solid #f4d26d; border-radius:8px; background:#fff8df; color:#7a5a00; font-size:12px; line-height:1.5; font-weight:800; }
    .side-nav { gap:0; }
    .side-home-group { border-top:1px solid #f2f4f7; border-bottom:1px solid #edf1f5; }
    .side-home-group > summary { list-style:none; }
    .side-home-group > summary::-webkit-details-marker { display:none; }
    .side-home-group[open] > summary .side-chevron { transform:rotate(180deg); }
    .side-home-group > summary:hover { background:#eef7ff; color:#1683e9; }
    .side-account-group { border-top:1px solid #f2f4f7; border-bottom:1px solid #edf1f5; }
    .side-account-group > summary { list-style:none; }
    .side-account-group > summary::-webkit-details-marker { display:none; }
    .side-account-group[open] > summary .side-chevron { transform:rotate(180deg); }
    .side-account-group > summary:hover { background:#eef7ff; color:#1683e9; }
    .side-home-group .side-item,.side-nav > .side-item,.app-sidebar > .side-item { min-height:52px; padding:0 24px; border-radius:0; }
    .home-subnav { display:grid; max-height:220px; overflow:hidden; padding:4px 0 8px; background:#fafbfc; opacity:1; transition:max-height .18s ease, opacity .18s ease, padding .18s ease; }
    .side-home-group:not([open]) .home-subnav { max-height:0; padding-top:0; padding-bottom:0; opacity:0; }
    .home-subnav a { min-height:42px; padding:0 24px 0 58px; display:flex; align-items:center; color:#526070; font-size:14px; font-weight:600; text-decoration:none; }
    .home-subnav a:hover { color:var(--accent-strong); background:#eef7ff; }
    .home-subnav a.active { color:var(--accent-strong); background:#eef7ff; box-shadow:inset 3px 0 0 var(--accent); }
    .account-subnav { display:grid; max-height:220px; overflow:hidden; padding:4px 0 8px; background:#fafbfc; opacity:1; transition:max-height .18s ease, opacity .18s ease, padding .18s ease; }
    .side-account-group:not([open]) .account-subnav { max-height:0; padding-top:0; padding-bottom:0; opacity:0; }
    .account-subnav a { min-height:42px; padding:0 24px 0 58px; display:flex; align-items:center; color:#526070; font-size:14px; font-weight:600; text-decoration:none; }
    .account-subnav a:hover { color:var(--accent-strong); background:#eef7ff; }
    .account-subnav a.active { color:var(--accent-strong); background:#eef7ff; box-shadow:inset 3px 0 0 var(--accent); }
    .side-nav > .side-item.active,.app-sidebar > .side-item.active { border-right:3px solid var(--accent); background:#e5f5ff; color:#1683e9; }
    .app-home { min-height:100vh; margin-left:220px; padding:20px 38px 48px; }
    .shell { margin-left:220px; }
    body[data-active-workspace="home-workspace"] .shell,
    body[data-active-workspace="select-workspace"] .shell,
    body[data-active-workspace="buy-workspace"] .shell,
    body[data-active-workspace="sell-workspace"] .shell,
    body[data-active-workspace="agent-workspace"] .shell,
    body[data-active-workspace="account-workspace"] .shell,
    body[data-active-workspace="plan-workspace"] .shell { display:none; }
    .restored-search { width:min(720px,100%); margin:0 auto; padding-top:min(12vh,96px); text-align:center; }
    .restored-search .hero-title { margin-bottom:72px; }
    .restored-search .hero-search { width:100%; }
    .symbol-presets { margin-top:16px; display:flex; justify-content:center; gap:22px; flex-wrap:wrap; }
    .symbol-presets button { border:0; border-radius:0; padding:0; background:transparent; color:#667085; font-size:12px; font-weight:700; cursor:pointer; }
    .symbol-presets button:hover { color:var(--accent-strong); }
    .search-result { width:min(1040px,calc(100vw - 320px)); margin:32px 0 0 50%; transform:translateX(-50%); text-align:left; }
    .search-result-head { display:flex; align-items:flex-end; justify-content:space-between; gap:16px; margin-bottom:14px; }
    .search-result-title { flex:1 1 auto; display:flex; align-items:flex-start; gap:10px; min-width:0; }
    .search-result-title > div { min-width:0; }
    .search-result-head h2 { margin:0 0 6px; color:#172033; font-size:22px; }
    .search-result-head p { margin:0; color:#667085; font-size:13px; }
    .search-result-head h2,.search-result-head p { overflow-wrap:anywhere; }
    .search-result-meta { flex:0 0 auto; color:#667085; font-size:12px; font-weight:700; white-space:nowrap; }
    .search-kpis { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; margin-bottom:14px; }
    .search-kpi { min-width:0; padding:14px 16px; border:1px solid #d9e1ea; border-radius:8px; background:#fff; }
    .search-kpi span { display:block; margin-bottom:6px; color:#667085; font-size:12px; }
    .search-kpi strong { display:block; color:#172033; font:900 21px/1.2 Consolas,"Microsoft YaHei",monospace; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    .search-result-grid { display:grid; grid-template-columns:1fr; gap:14px; align-items:start; }
    .result-panel .report-grid-2 { grid-template-columns:1fr; }
    .buy-data-table,.history-chart-panel { border:1px solid #d9e1ea; border-radius:8px; background:#fff; overflow:hidden; }
    .buy-data-table h3,.history-chart-panel h3 { margin:0; padding:13px 15px; border-bottom:1px solid #edf1f5; color:#273444; font-size:15px; }
    .buy-metric-strip { display:flex; gap:10px; padding:12px 14px; overflow-x:auto; scrollbar-gutter:stable; }
    .buy-metric { flex:0 0 148px; min-height:92px; padding:12px; border:1px solid #edf1f5; border-radius:8px; background:#fbfdff; display:grid; align-content:start; gap:6px; cursor:grab; user-select:none; }
    .buy-metric:active { cursor:grabbing; }
    .buy-metric.dragging { opacity:.45; border-color:#69aef5; background:#eef7ff; }
    .buy-metric.drop-before { box-shadow:-3px 0 0 #1676d2; }
    .buy-metric span { color:#667085; font-size:12px; line-height:1.35; }
    .buy-metric strong { color:#172033; font:900 18px/1.2 Consolas,"Microsoft YaHei",monospace; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    .buy-metric small { color:#667085; font-size:11px; line-height:1.35; }
    .history-chart-panel img { width:100%; min-height:300px; max-height:560px; object-fit:contain; display:block; background:#fff; }
    .history-chart-head { min-height:48px; padding:10px 14px; border-bottom:1px solid #edf1f5; display:flex; align-items:center; justify-content:space-between; gap:12px; }
    .history-chart-head h3 { padding:0; border:0; }
    .history-range-tabs { display:flex; align-items:center; gap:6px; flex-wrap:wrap; }
    .history-range-tabs button { min-height:30px; padding:0 10px; border:1px solid #d9e1ea; border-radius:6px; background:#fff; color:#475467; font-size:12px; font-weight:800; cursor:pointer; }
    .history-range-tabs button.active,.history-range-tabs button:hover { border-color:#69aef5; background:#eef7ff; color:#1676d2; }
    .split-chart-stack { display:grid; gap:12px; padding:14px; }
    .chart-board { border:1px solid #edf1f5; border-radius:8px; background:#fff; overflow:hidden; }
    .chart-board-title { padding:9px 12px; border-bottom:1px solid #edf1f5; color:#475467; font-size:12px; font-weight:800; display:flex; align-items:center; justify-content:space-between; gap:12px; }
    .chart-board-title > span:first-child { min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    .chart-board svg { width:100%; display:block; background:#fff; }
    .price-chart svg { height:390px; }
    .price-chart svg { cursor:crosshair; }
    .chart-hit-layer { fill:transparent; pointer-events:all; }
    .chart-crosshair-line { stroke:#1676d2; stroke-width:1.2; stroke-dasharray:5 5; pointer-events:none; }
    .chart-crosshair-point { fill:#1676d2; stroke:#fff; stroke-width:3; pointer-events:none; }
    .chart-crosshair-label { pointer-events:none; }
    .indicator-chart svg { height:170px; }
    .chart-legend { display:flex; flex-wrap:wrap; gap:12px; padding:0 14px 12px; color:#667085; font-size:12px; }
    .chart-legend span { display:flex; align-items:center; gap:5px; }
    .chart-legend i { width:18px; height:2px; display:block; background:#1d4ed8; }
    .chart-legend span:nth-child(2) i { background:#f59e0b; }
    .chart-legend span:nth-child(3) i { background:#16a34a; }
    .inline-chart-legend { display:flex; align-items:center; justify-content:flex-end; gap:10px; flex-wrap:wrap; font-size:11px; font-weight:700; color:#667085; }
    .inline-chart-legend span { display:inline-flex; align-items:center; gap:5px; white-space:nowrap; }
    .inline-chart-legend i { width:16px; height:2px; display:block; background:#1d4ed8; }
    .inline-chart-legend .ma20 i { background:#f59e0b; }
    .inline-chart-legend .ma60 i { background:#16a34a; }
    .inline-chart-legend .rsi i { background:#8b5cf6; }
    .inline-chart-legend .rsi-high i { height:0; border-top:2px dashed #ef4444; background:transparent; }
    .inline-chart-legend .rsi-low i { height:0; border-top:2px dashed #22c55e; background:transparent; }
    .chart-empty { min-height:240px; padding:34px 16px; color:#667085; display:grid; place-items:center; text-align:center; }
    .broker-empty-panel { width:min(620px,100%); padding:22px; border:1px dashed #cfd9e6; border-radius:8px; background:#fbfdff; color:#667085; text-align:left; line-height:1.65; }
    .broker-empty-panel strong { display:block; margin-bottom:7px; color:#172033; font-size:16px; }
    .broker-empty-panel span { display:block; font-size:13px; }
    .broker-empty-panel code { padding:2px 5px; border-radius:4px; background:#eef2f6; color:#344054; font-family:Consolas,monospace; }
    .broker-status-line { margin-top:10px; color:#475467; font-size:12px; font-weight:800; }
    .history-chart-empty { padding:40px 16px; color:#667085; text-align:center; }
    .signal-note { margin-top:10px; padding:10px 12px; border-left:3px solid #69aef5; background:#f8fbff; color:#475467; font-size:13px; line-height:1.55; }
    .watchlist-workspace { width:min(1080px,100%); margin:28px auto 0; text-align:left; }
    .watchlist-head { display:flex; align-items:flex-end; justify-content:space-between; gap:18px; margin-bottom:18px; }
    .watchlist-head h1 { color:var(--accent); font-size:30px; font-weight:500; }
    .watchlist-head p { margin-top:6px; color:#667085; font-size:13px; }
    .watchlist-tools { display:flex; align-items:center; gap:8px; }
    .watchlist-tools select,.watchlist-tools button { min-height:38px; border:1px solid #d9e1ea; border-radius:6px; background:#fff; color:#344054; font:700 13px/1 "Microsoft YaHei",sans-serif; }
    .watchlist-tools select { min-width:150px; padding:0 34px 0 12px; }
    .watchlist-tools button { padding:0 14px; cursor:pointer; }
    .watchlist-search { width:100%; margin-bottom:14px; }
    .rule-disclosure { margin-bottom:14px; border:1px solid #d9e1ea; border-radius:6px; background:#fff; }
    .rule-disclosure summary { min-height:44px; padding:0 14px; display:flex; align-items:center; justify-content:space-between; list-style:none; color:#344054; font-weight:800; cursor:pointer; }
    .rule-disclosure summary::-webkit-details-marker { display:none; }
    .rule-disclosure summary::after { content:"+"; color:#667085; font-size:18px; }
    .rule-disclosure[open] summary::after { content:"-"; }
    .rule-body { padding:0 14px 14px; display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:8px 18px; color:#667085; font-size:12px; line-height:1.6; }
    .rule-body b { color:#344054; }
    .custom-rule-editor { display:none; grid-column:1 / -1; gap:8px; margin-top:6px; }
    .custom-rule-editor.active { display:grid; }
    .custom-rule-editor textarea { min-height:76px; resize:vertical; }
    .custom-rule-editor button { width:max-content; }
    .rule-feedback { color:#087443; font-weight:700; }
    .watchlist-table-wrap { overflow:auto; border:1px solid #d9e1ea; border-radius:8px; background:#fff; }
    .watchlist-table { width:100%; min-width:960px; border-collapse:separate; border-spacing:0; font-size:13px; }
    .watchlist-table th { position:sticky; top:0; z-index:1; height:46px; padding:0 12px; border-bottom:1px solid #d9e1ea; background:#f8fafc; color:#475467; text-align:right; white-space:nowrap; }
    .watchlist-table th:first-child,.watchlist-table td:first-child { position:sticky; left:0; text-align:left; font-weight:800; }
    .watchlist-table th:first-child { z-index:2; background:#f8fafc; }
    .watchlist-table td { height:48px; padding:0 12px; border-bottom:1px solid rgba(255,255,255,.55); text-align:right; white-space:nowrap; }
    .watchlist-table tbody tr:last-child td { border-bottom:0; }
    .watchlist-name-cell { display:flex; align-items:center; justify-content:space-between; gap:10px; }
    .watchlist-name-main { display:grid; gap:2px; min-width:0; }
    .watchlist-name-main strong { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:#172033; font-size:13px; }
    .watchlist-name-main small { color:#667085; font:700 11px/1.2 Consolas,"Microsoft YaHei",monospace; }
    .favorite-remove { width:28px; height:28px; flex:0 0 28px; border:1px solid #f4c95d; border-radius:5px; display:grid; place-items:center; background:#fff7d6; color:#d69e00; cursor:pointer; }
    .favorite-remove:hover { border-color:#f3a19a; background:#fff1f0; color:#dc2626; }
    .favorite-remove .ui-icon { width:15px; height:15px; fill:currentColor; }
    .watchlist-empty { padding:42px 20px; border-top:1px solid #e5eaf0; background:#fff; color:#667085; text-align:center; }
    .watchlist-empty strong { display:block; margin-bottom:6px; color:#273444; font-size:15px; }
    .watchlist-table tr.status-low td { background:#e9f8ef; }
    .watchlist-table tr.status-normal td { background:#fff5d9; }
    .watchlist-table tr.status-high td { background:#ffebe8; }
    .watchlist-table tr.status-low td:first-child { background:#e9f8ef; }
    .watchlist-table tr.status-normal td:first-child { background:#fff5d9; }
    .watchlist-table tr.status-high td:first-child { background:#ffebe8; }
    .valuation-label { display:inline-flex; align-items:center; gap:6px; font-weight:900; }
    .valuation-label::before { content:""; width:7px; height:7px; border-radius:50%; background:#16a34a; }
    .status-normal .valuation-label::before { background:#d69e00; }
    .status-high .valuation-label::before { background:#dc2626; }
    .stars { color:#e6a700; letter-spacing:0; font-size:14px; }
    .stale-value { color:#b54708; font-weight:800; }
    .blank-value { color:#98a2b3; }
    .table-legend { display:flex; flex-wrap:wrap; gap:14px; margin-top:10px; color:#667085; font-size:12px; }
    .table-legend span { display:flex; align-items:center; gap:6px; }
    .table-legend i { width:10px; height:10px; border-radius:3px; background:#a7e0b8; }
    .table-legend span:nth-child(2) i { background:#f4d26d; }
    .table-legend span:nth-child(3) i { background:#f3a19a; }
    .indicator-workspace { width:min(940px,100%); margin:92px auto 0; }
    .workspace-title { margin:0 0 20px; color:var(--accent); font-size:34px; line-height:1.2; font-weight:500; }
    .workspace-title-row { margin-bottom:20px; display:flex; align-items:center; justify-content:space-between; gap:16px; }
    .workspace-title-row .workspace-title { margin:0; }
    .favorite-current { min-height:40px; padding:0 15px; border:1px solid #cfd9e6; border-radius:6px; display:inline-flex; align-items:center; gap:8px; background:#fff; color:#344054; font-size:13px; font-weight:800; cursor:pointer; }
    .favorite-current:hover,.favorite-current.active { border-color:#69aef5; background:#eef7ff; color:#1676d2; }
    .favorite-current .ui-icon { width:17px; height:17px; fill:none; }
    .favorite-current.active .ui-icon { fill:currentColor; }
    .favorite-overview { width:40px; height:40px; min-width:40px; min-height:40px; padding:0; border-radius:6px; }
    .favorite-overview .favorite-text { position:absolute; width:1px; height:1px; padding:0; margin:-1px; overflow:hidden; clip:rect(0,0,0,0); white-space:nowrap; border:0; }
    .agent-workspace { width:min(940px,100%); margin:72px auto 0; }
    .agent-workspace-head { margin-bottom:22px; }
    .agent-workspace-head h1 { margin:0 0 7px; color:#172033; font-size:28px; }
    .agent-workspace-head p { margin:0; color:#667085; }
    .agent-builder-grid { display:grid; grid-template-columns:minmax(0,1.45fr) minmax(260px,.75fr); gap:18px; align-items:start; }
    .agent-builder,.agent-preview { border:1px solid #d9e1ea; border-radius:8px; background:#fff; }
    .agent-builder { padding:20px; }
    .agent-form-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:15px; }
    .agent-field { display:grid; gap:7px; }
    .agent-field.full { grid-column:1 / -1; }
    .agent-field label { color:#344054; font-size:12px; font-weight:800; }
    .agent-field input,.agent-field select,.agent-field textarea { width:100%; border:1px solid #d9e1ea; border-radius:6px; background:#fff; color:#172033; font:13px/1.5 "Microsoft YaHei",sans-serif; }
    .agent-field input,.agent-field select { min-height:42px; padding:0 12px; }
    .agent-field textarea { min-height:96px; padding:10px 12px; resize:vertical; }
    .agent-options { display:flex; flex-wrap:wrap; gap:8px; }
    .agent-options label { min-height:36px; padding:0 11px; border:1px solid #d9e1ea; border-radius:6px; display:flex; align-items:center; gap:7px; color:#475467; font-weight:700; cursor:pointer; }
    .agent-options input { width:auto; min-height:auto; margin:0; }
    .agent-actions { margin-top:18px; display:flex; align-items:center; gap:12px; }
    .agent-actions button { min-height:42px; padding:0 18px; border:0; border-radius:6px; background:#2867e8; color:#fff; font-weight:800; cursor:pointer; }
    .agent-build-feedback { color:#087443; font-size:12px; font-weight:700; }
    .agent-preview { overflow:hidden; }
    .agent-preview h2 { margin:0; padding:16px 18px; border-bottom:1px solid #e5eaf0; font-size:16px; }
    .agent-preview-list { margin:0; padding:4px 18px; list-style:none; }
    .agent-preview-list li { padding:13px 0; border-bottom:1px solid #edf1f5; display:flex; justify-content:space-between; gap:16px; color:#667085; font-size:12px; }
    .agent-preview-list li:last-child { border-bottom:0; }
    .agent-preview-list strong { color:#273444; text-align:right; }
    .agent-transparency { margin:0 18px 18px; padding:12px; border-left:3px solid #69aef5; background:#f8fbff; color:#667085; font-size:12px; line-height:1.6; }
    .created-agent-panel { margin:0 18px 18px; border-top:1px solid #edf1f5; padding-top:14px; }
    .created-agent-head { margin-bottom:10px; display:flex; align-items:center; justify-content:space-between; gap:12px; }
    .created-agent-head h3 { margin:0; color:#172033; font-size:14px; }
    .created-agent-head span { color:#667085; font-size:12px; font-weight:800; }
    .created-agent-list { display:grid; gap:10px; max-height:260px; overflow:auto; }
    .created-agent-empty { padding:18px 12px; border:1px dashed #d9e1ea; border-radius:8px; color:#667085; text-align:center; font-size:12px; }
    .created-agent-item { padding:12px; border:1px solid #edf1f5; border-radius:8px; background:#fbfdff; display:grid; gap:8px; }
    .created-agent-item strong { min-width:0; color:#172033; font-size:13px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    .created-agent-meta { display:flex; flex-wrap:wrap; gap:8px; color:#667085; font-size:11px; }
    .created-agent-actions { display:flex; gap:8px; }
    .created-agent-actions button { min-height:28px; padding:0 9px; border:1px solid #d9e1ea; border-radius:6px; background:#fff; color:#475467; font-size:12px; font-weight:800; cursor:pointer; }
    .created-agent-actions button:hover { border-color:#69aef5; color:#1676d2; background:#eef7ff; }
    .created-agent-build { width:100%; min-height:36px; margin-top:12px; border:1px solid #69aef5; border-radius:6px; background:#eef7ff; color:#1676d2; font-size:13px; font-weight:800; cursor:pointer; }
    .created-agent-build:hover { background:#dff0ff; }
    .plan-workspace { width:min(980px,100%); margin:56px auto 0; }
    .plan-quote { margin:0 0 10px; color:#2f8ff0; font-size:13px; font-weight:800; letter-spacing:.04em; }
    .plan-head h1 { margin:0 0 10px; color:#172033; font-size:30px; }
    .plan-head p { margin:0; color:#667085; }
    .plan-panel { margin-top:22px; padding:20px; border:1px solid #d9e1ea; border-radius:8px; background:#fff; }
    .plan-mode-row { display:flex; align-items:center; gap:10px; margin-bottom:16px; }
    .plan-mode-button { min-height:36px; padding:0 14px; border:1px solid #d9e1ea; border-radius:999px; background:#fff; color:#344054; font-size:13px; font-weight:800; cursor:pointer; }
    .plan-mode-button.active { border-color:#69aef5; background:#eef7ff; color:#1676d2; }
    .plan-template-box { margin-bottom:14px; padding:14px 16px; border:1px solid #e5eaf0; border-radius:8px; background:#f8fbff; color:#475467; line-height:1.7; white-space:pre-wrap; }
    .plan-editor { width:100%; min-height:420px; padding:18px; border:1px solid #d9e1ea; border-radius:8px; background:#fff; color:#172033; font:14px/1.75 "Microsoft YaHei","PingFang SC",Arial,sans-serif; resize:vertical; }
    .plan-meta { margin-top:12px; color:#667085; font-size:12px; }
    .account-workspace { width:min(760px,100%); margin:72px auto 0; }
    .account-card { border:1px solid #d9e1ea; border-radius:8px; background:#fff; padding:22px; display:flex; align-items:center; gap:18px; }
    .account-avatar { width:72px; height:72px; border-radius:999px; display:grid; place-items:center; background:#e5f5ff; color:#1676d2; font-size:30px; font-weight:900; }
    .account-info { min-width:0; }
    .account-info span { display:block; margin-bottom:6px; color:#667085; font-size:13px; font-weight:800; }
    .account-info strong { display:block; color:#172033; font-size:24px; line-height:1.2; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    .workspace-search { margin-bottom:26px; }
    .workspace-grid { display:grid; grid-template-columns:minmax(0,1.55fr) minmax(230px,.75fr); gap:20px; align-items:start; }
    .metric-selector { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; }
    .metric-option { min-height:54px; padding:10px 14px; border:1px solid #d9e1ea; border-radius:6px; display:flex; align-items:center; justify-content:center; gap:9px; background:#fff; color:#273444; font-size:14px; font-weight:700; cursor:pointer; transition:border-color .15s ease,background .15s ease,color .15s ease,box-shadow .15s ease; }
    .metric-option:hover,.metric-option.active { border-color:#69aef5; background:#eef7ff; color:#1676d2; box-shadow:0 4px 12px rgba(47,143,240,.08); }
    .metric-option:first-child { grid-column:1 / -1; }
    .metric-option .ui-icon { width:17px; height:17px; }
    .valuation-table { margin-top:14px; border:1px solid #d9e1ea; border-radius:6px; overflow:hidden; background:#fff; }
    .valuation-row { min-height:48px; display:grid; grid-template-columns:minmax(150px,1.5fr) repeat(3,minmax(80px,1fr)); align-items:center; border-bottom:1px solid #e5eaf0; }
    .valuation-row:last-child { border-bottom:0; }
    .valuation-row > span { min-width:0; height:100%; padding:12px 14px; display:flex; align-items:center; border-right:1px solid #e5eaf0; }
    .valuation-row > span:last-child { border-right:0; }
    .valuation-row.head { min-height:40px; background:#f8fafc; color:#667085; font-size:12px; font-weight:800; }
    .valuation-row:not(.head) > span:not(:first-child) { justify-content:flex-end; font-family:Consolas,"Microsoft YaHei",monospace; }
    .secondary-metric { min-height:54px; padding:12px 16px; border:1px solid #d9e1ea; border-radius:6px; display:flex; align-items:center; justify-content:center; gap:10px; background:#fff; color:#273444; font-size:14px; font-weight:700; }
    .secondary-note { margin-top:12px; padding:14px 16px; border-left:3px solid #8cbdf2; background:#f8fbff; color:#667085; font-size:13px; line-height:1.65; }
    .sell-workspace { width:min(940px,100%); margin:72px auto 0; }
    .sell-head { margin-bottom:20px; }
    .sell-head h1 { margin:0 0 7px; color:var(--accent); font-size:30px; font-weight:500; }
    .sell-head p { margin:0; color:#667085; font-size:13px; }
    .sell-strategy-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:14px; }
    .sell-card { min-height:138px; padding:18px; border:1px solid #d9e1ea; border-radius:8px; background:#fff; cursor:pointer; transition:border-color .15s ease,background .15s ease,box-shadow .15s ease; }
    .sell-card:hover,.sell-card.active { border-color:#69aef5; background:#f8fbff; box-shadow:0 12px 28px rgba(47,143,240,.08); }
    .sell-card h2 { margin:0 0 8px; color:#172033; font-size:17px; }
    .sell-card p { margin:0; color:#667085; font-size:13px; line-height:1.65; }
    .sell-rule-panel { margin-top:16px; padding:18px; border:1px solid #d9e1ea; border-radius:8px; background:#fff; }
    .sell-rule-panel h2 { margin:0 0 12px; font-size:17px; }
    .sell-rule-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; }
    .sell-rule-field { display:grid; gap:7px; }
    .sell-rule-field label { color:#344054; font-size:12px; font-weight:800; }
    .sell-rule-field input,.sell-rule-field select,.sell-rule-field textarea { min-height:40px; border:1px solid #d9e1ea; border-radius:6px; padding:0 10px; background:#fff; color:#172033; font:13px/1.5 "Microsoft YaHei",sans-serif; }
    .sell-rule-field textarea { min-height:82px; padding:10px; resize:vertical; }
    .sell-rule-field.full { grid-column:1 / -1; }
    .backtest-header { margin:28px 0 12px; display:flex; align-items:center; justify-content:space-between; gap:16px; }
    .backtest-heading { display:flex; align-items:center; gap:9px; color:#273444; font-size:16px; font-weight:900; }
    .backtest-heading .ui-icon { color:var(--accent-strong); }
    .backtest-scales { display:flex; align-items:center; gap:6px; }
    .backtest-scale { min-height:30px; padding:0 10px; border:1px solid #d9e1ea; border-radius:6px; background:#fff; color:#475467; font-size:12px; font-weight:800; cursor:pointer; }
    .backtest-scale:hover,.backtest-scale.active { border-color:#69aef5; background:#eef7ff; color:#1676d2; }
    .workspace-chart { padding:16px; border:1px solid #d9e1ea; border-radius:6px; background:#fff; }
    .workspace-chart svg { width:100%; height:360px; display:block; }
    .workspace-chart .chart-axis { fill:none; stroke:#98a2b3; stroke-width:1; }
    .workspace-chart .chart-tick { fill:#667085; font-size:11px; font-family:"Microsoft YaHei",sans-serif; }
    .workspace-chart .chart-axis-title { fill:#475467; font-size:12px; font-weight:700; font-family:"Microsoft YaHei",sans-serif; }
    .workspace-chart-legend { display:flex; flex-wrap:wrap; gap:16px; margin-top:12px; color:#667085; font-size:12px; }
    .workspace-chart-legend span { display:flex; align-items:center; gap:6px; }
    .workspace-chart-legend i { width:18px; height:2px; display:block; background:#2563eb; }
    .workspace-chart-legend span:nth-child(2) i { background:#f59e0b; }
    .workspace-chart-legend span:nth-child(3) i { background:#93c5fd; }
    .submit-card {
      border-color:var(--border);
      border-radius:var(--radius-lg);
      box-shadow:0 18px 44px rgba(16,24,40,.12);
    }
    @media (max-width:900px) {
      .app-sidebar { background:#fff; }
      .side-item.active,.side-item:hover { background:#e5f5ff; }
      .app-sidebar { width:auto; padding:12px 16px; }
      .side-home-group { display:block; min-width:0; border:0; }
      .side-account-group { display:block; min-width:0; border:0; }
      .side-home-group .side-item,.side-nav > .side-item,.app-sidebar > .side-item { min-height:34px; padding:0 8px; border-radius:var(--radius); }
      .home-subnav { display:none; }
      .account-subnav { display:none; }
      .side-nav > .side-item.active,.app-sidebar > .side-item.active { border-right:0; }
      .app-home { min-height:auto; margin-left:0; padding:18px 16px 36px; }
      .shell { margin-left:0; }
      .restored-search { padding-top:52px; }
      .restored-search .hero-title { margin-bottom:38px; }
      .search-result { width:100%; margin-left:0; transform:none; }
      .search-kpis,.search-result-grid { grid-template-columns:1fr; }
      .search-result-head { align-items:flex-start; flex-direction:column; }
      .search-result-title { width:100%; }
      .watchlist-workspace { margin-top:20px; }
      .watchlist-head { align-items:flex-start; flex-direction:column; }
      .watchlist-tools { width:100%; }
      .watchlist-tools select { flex:1; min-width:0; }
      .rule-body { grid-template-columns:1fr; }
      .indicator-workspace { margin-top:64px; }
      .workspace-title-row { align-items:flex-start; }
      .symbol-presets { gap:14px; }
      .sell-workspace { margin-top:28px; }
      .sell-strategy-grid,.sell-rule-grid { grid-template-columns:1fr; }
      .sell-rule-field.full { grid-column:auto; }
      .backtest-header { align-items:flex-start; flex-direction:column; }
      .backtest-scales { width:100%; overflow:auto; padding-bottom:2px; }
      .history-chart-head { align-items:flex-start; flex-direction:column; }
      .history-range-tabs { width:100%; overflow:auto; flex-wrap:nowrap; padding-bottom:2px; }
      .price-chart svg { height:300px; }
      .indicator-chart svg { height:150px; }
      .agent-workspace { margin-top:28px; }
      .agent-builder-grid,.agent-form-grid { grid-template-columns:1fr; }
      .agent-field.full { grid-column:auto; }
      .plan-panel { padding:14px; }
      .plan-editor { min-height:300px; }
      .workspace-title { font-size:28px; }
      .workspace-grid { grid-template-columns:1fr; gap:14px; }
      .metric-selector { grid-template-columns:1fr; }
      .metric-option:first-child { grid-column:auto; }
      .valuation-row { grid-template-columns:minmax(125px,1.3fr) repeat(3,minmax(62px,1fr)); font-size:12px; }
      .valuation-row > span { padding:10px 8px; }
      .workspace-chart { padding:10px; overflow:hidden; }
      .workspace-chart svg { height:210px; }
      .result-panel { padding:16px; }
      .right-rail section,.right-rail details { padding:14px; }
      .reader-main .reader-switch { grid-template-columns:1fr; }
      .report-grid-2 { gap:12px; }
      .workflow { gap:8px; }
    }
  </style>
</head>
<body class="module-analysis">
  <svg class="icon-sprite" aria-hidden="true" focusable="false">
    <symbol id="icon-chart" viewBox="0 0 24 24"><path d="M4 19V5"/><path d="M4 19h16"/><path d="m7 15 4-4 3 3 5-7"/></symbol>
    <symbol id="icon-home" viewBox="0 0 24 24"><path d="m3 11 9-8 9 8"/><path d="M5 10v10h14V10"/><path d="M9 20v-6h6v6"/></symbol>
    <symbol id="icon-agent" viewBox="0 0 24 24"><rect x="4" y="7" width="16" height="13" rx="3"/><path d="M12 3v4"/><circle cx="9" cy="13" r="1"/><circle cx="15" cy="13" r="1"/><path d="M9 17h6"/></symbol>
    <symbol id="icon-sliders" viewBox="0 0 24 24"><path d="M4 6h10"/><path d="M18 6h2"/><path d="M14 4v4"/><path d="M4 12h3"/><path d="M11 12h9"/><path d="M7 10v4"/><path d="M4 18h8"/><path d="M16 18h4"/><path d="M12 16v4"/></symbol>
    <symbol id="icon-briefcase" viewBox="0 0 24 24"><rect x="3" y="7" width="18" height="13" rx="2"/><path d="M9 7V4h6v3"/><path d="M3 12h18"/><path d="M10 12v2h4v-2"/></symbol>
    <symbol id="icon-star" viewBox="0 0 24 24"><path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2-5.6-3-5.6 3 1.1-6.2L3 9.6l6.2-.9Z"/></symbol>
    <symbol id="icon-history" viewBox="0 0 24 24"><path d="M3 12a9 9 0 1 0 3-6.7"/><path d="M3 4v5h5"/><path d="M12 7v5l3 2"/></symbol>
    <symbol id="icon-user" viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></symbol>
    <symbol id="icon-chevron-right" viewBox="0 0 24 24"><path d="m9 18 6-6-6-6"/></symbol>
    <symbol id="icon-chevron-down" viewBox="0 0 24 24"><path d="m6 9 6 6 6-6"/></symbol>
    <symbol id="icon-send" viewBox="0 0 24 24"><path d="M3.4 2.8a1 1 0 0 1 1.1-.1l16.6 8.4a1 1 0 0 1 0 1.8L4.5 21.3a1 1 0 0 1-1.4-1.1l1.3-6.1 8.7-2.1-8.7-2.1-1.3-6.1a1 1 0 0 1 .3-1Z"/></symbol>
  </svg>
  <aside class="app-sidebar" aria-label="主导航">
    <div class="sidebar-disclaimer">不构成投资建议，仅用于数据分析和复盘。</div>
    <nav class="side-nav">
      <details class="side-home-group" open>
        <summary class="side-item active" data-workspace-target="home-workspace" data-home-summary aria-expanded="true"><svg class="ui-icon nav-icon"><use href="#icon-home"/></svg><span>首页</span><svg class="ui-icon side-chevron"><use href="#icon-chevron-down"/></svg></summary>
        <div class="home-subnav"><a href="#select-workspace" data-workspace-target="select-workspace">关注池</a><a href="#buy-workspace" data-workspace-target="buy-workspace">指标</a><a href="#sell-workspace" data-workspace-target="sell-workspace">风控</a><a href="#agent-workspace" data-workspace-target="agent-workspace">追问</a></div>
      </details>
    </nav>
    <div class="side-spacer"></div>
    <details class="side-account-group">
      <summary class="side-item" data-account-summary data-workspace-target="account-workspace" aria-expanded="false"><svg class="ui-icon nav-icon"><use href="#icon-user"/></svg><span>我的</span><svg class="ui-icon side-chevron"><use href="#icon-chevron-down"/></svg></summary>
      <div class="account-subnav"><a href="#plan-workspace" data-workspace-target="plan-workspace">计划</a></div>
    </details>
  </aside>
  <main class="app-home" aria-label="指标工作台">
    <section class="restored-search" id="home-workspace" data-workspace-view>
      <h1 class="hero-title">把一次复盘讲清楚</h1>
      <form method="post" class="hero-search" aria-label="首页搜索">
        <input type="hidden" name="mode" value="analyze">
        <input type="hidden" name="market" value="auto">
        <input type="hidden" name="period" value="{{ form.period }}">
        <input type="hidden" name="start_date" value="{{ form.start_date }}">
        <input type="hidden" name="end_date" value="{{ form.end_date }}">
        <input type="hidden" name="use_ai" value="{{ 'true' if form.use_ai else 'false' }}">
        <input type="hidden" name="reader_version" value="个人投资者版">
        <input id="homeSymbol" name="symbol" type="text" value="{{ form.symbol if result else '' }}" placeholder="输入基金、股票或指数代码" autocomplete="off">
        <button type="submit" aria-label="开始分析"><svg class="ui-icon hero-submit-icon" aria-hidden="true"><use href="#icon-send"/></svg></button>
      </form>
      <div class="symbol-presets"><button type="button" data-symbol-preset="000300">沪深300</button><button type="button" data-symbol-preset="270048">广发纯债债券A</button><button type="button" data-symbol-preset="000905">中证500</button><button type="button" data-symbol-preset="008042">008042</button><button type="button" data-symbol-preset="018524">018524</button></div>
      {% if result %}
      <div class="search-result" aria-label="搜索结果数据">
        <div class="search-result-head">
          <div class="search-result-title">
            <button class="favorite-current favorite-overview" type="button" data-favorite-toggle data-symbol="{{ result.symbol }}" data-name="{{ result.display_name or result.symbol }}" data-watchlist-item='{{ result.watchlist_item|tojson|forceescape }}' title="收藏到挑选" aria-label="收藏到挑选">
              <svg class="ui-icon" aria-hidden="true"><use href="#icon-star"/></svg><span class="favorite-text">收藏到挑选</span>
            </button>
            <div><h2>{{ result.display_name or result.symbol }}{% if result.display_name and result.display_name != result.symbol %} {{ result.symbol }}{% endif %} 这次复盘</h2><p>{{ result.market_label }} · {{ result.data_range }} · {{ result.data_points }} 条历史数据</p></div>
          </div>
          <div class="search-result-meta">更新：{{ result.generated_at }}</div>
        </div>
        <div class="search-kpis">
          <div class="search-kpi"><span>{{ result.unit_label }}</span><strong>{{ result.latest_price or '-' }}</strong></div>
          <div class="search-kpi"><span>日变化</span><strong>{{ result.summary.change_pct }}</strong></div>
          <div class="search-kpi"><span>近一年位置</span><strong>{{ result.summary.position }}</strong></div>
          <div class="search-kpi"><span>距近一年高点</span><strong>{{ result.summary.drawdown }}</strong></div>
        </div>
        <div class="evidence-note">{{ result.summary.evidence_note }}</div>
        <div class="search-result-grid">
          <section class="buy-data-table" aria-label="复盘证据">
            <h3>复盘证据</h3>
            <div class="buy-metric-strip" role="list">
              {% for row in result.summary.buy_rows %}
              <div class="buy-metric" role="listitem" data-metric-key="{{ row.label }}" draggable="true" tabindex="0"><span>{{ row.label }}</span><strong>{{ row.value }}</strong><small>{{ row.note }}</small></div>
              {% endfor %}
            </div>
            <div class="signal-note">{{ result.summary.signal_text }}</div>
          </section>
          <section class="history-chart-panel" aria-label="实时复盘图">
            <div class="history-chart-head">
              <h3>实时复盘图</h3>
              <div class="history-range-tabs" aria-label="历史走势图时间范围">
                <button type="button" class="active" data-history-range="live">最新</button>
                <button type="button" data-history-range="1m">一个月</button>
                <button type="button" data-history-range="1y">一年</button>
                <button type="button" data-history-range="10y">十年</button>
                <button type="button" data-history-range="all">至今</button>
              </div>
            </div>
            <script type="application/json" class="history-chart-data">{{ result.history_points|tojson }}</script>
            <div class="split-chart-stack" data-split-history-chart>
              <div class="chart-board price-chart"><div class="chart-board-title"><span>{{ result.unit_label }} / 均线</span><div class="inline-chart-legend" aria-label="价格图图例"><span><i></i>价格/净值</span><span class="ma20"><i></i>MA20</span><span class="ma60"><i></i>MA60</span></div></div><svg viewBox="0 0 980 390" role="img" aria-label="{{ result.symbol }} 价格走势图"></svg></div>
              <div class="chart-board indicator-chart"><div class="chart-board-title"><span>RSI</span><div class="inline-chart-legend" aria-label="RSI 图例"><span class="rsi"><i></i>RSI</span><span class="rsi-high"><i></i>70</span><span class="rsi-low"><i></i>30</span></div></div><svg viewBox="0 0 980 170" role="img" aria-label="{{ result.symbol }} RSI 指标图"></svg></div>
            </div>
            <div class="chart-legend"><span><i></i>价格/净值</span><span><i></i>MA20</span><span><i></i>MA60</span></div>
          </section>
        </div>
      </div>
      {% endif %}
    </section>
    <section class="watchlist-workspace" id="select-workspace" data-workspace-view hidden>
      <div class="watchlist-head">
        <div><h1>我的关注</h1><p>把常看的标的放在一起，集中比较趋势、回撤、位置和数据新鲜度。</p></div>
        <div class="watchlist-tools"><select id="valuationRule" aria-label="复盘口径"><option value="general">通用复盘口径</option><option value="custom">自定义口径</option></select><button type="button" id="refreshValuation">刷新状态</button></div>
      </div>
      <details class="rule-disclosure">
        <summary>数据口径与状态说明</summary>
        <div class="rule-body">
          <div><b>当前状态：</b>基金和指数主要根据近一年位置、回撤、RSI、20日/60日均线给出“高位回撤、接近超卖、趋势偏强”等观察状态。</div><div><b>绿色：</b>趋势或位置相对友好，适合继续跟踪，不代表买入建议。</div>
          <div><b>黄色：</b>状态需要复核，常见于高位回撤、趋势偏弱或信息不足。</div><div><b>红色：</b>过热、超卖或回撤较深，提醒先看风险和数据质量。</div>
          <div><b>股票估值：</b>只有拿到 PE、PB、股息率、ROE 等结构化字段时，才展示估值相关列。</div><div><b>行情字段：</b>当前值、近一年位置、距高点、RSI 和均线来自本次刷新后的行情数据。</div>
          <div><b>星级：</b>仅作为结构化估值数据充足时的辅助标签；没有可靠数据时留空。</div>
          <div class="custom-rule-editor"><textarea id="customRuleText" placeholder="输入自己的复盘口径，例如：近一年位置高于 80% 且 RSI 低于 45 时标记为高位回撤。"></textarea><button type="button" id="saveCustomRule">保存自定义口径</button><span class="rule-feedback" id="ruleFeedback"></span></div>
        </div>
      </details>
      <div class="watchlist-table-wrap">
        <table class="watchlist-table" aria-label="收藏标的估值表">
          <thead><tr id="watchlistHeader"><th>关注标的</th><th>当前状态</th><th>最新值</th><th>市盈率</th><th>市净率</th><th>近一年位置</th><th>距高点</th><th>RSI</th><th>20日均线</th><th>60日均线</th><th>场内基金</th><th>场外基金</th></tr></thead>
          <tbody id="watchlistBody"></tbody>
        </table>
      <div class="watchlist-empty" id="watchlistEmpty"><strong>还没有关注标的</strong>先在首页复盘结果左上角点亮收藏，后续可以集中比较趋势、回撤和数据新鲜度。</div>
      </div>
      <div class="table-legend"><span><i></i>趋势友好 / 继续跟踪</span><span><i></i>需要复核 / 观察为主</span><span><i></i>风险升高 / 先看风险</span></div>
    </section>
    <section class="indicator-workspace" id="buy-workspace" data-workspace-view hidden>
      <div class="workspace-title-row"><h1 class="workspace-title">指标</h1><button class="favorite-current" id="favoriteCurrent" type="button" data-favorite-toggle data-symbol="{{ result.symbol if result else (form.symbol or '000300') }}" data-name="{{ result.display_name if result else (form.symbol or '沪深300') }}" data-watchlist-item='{% if result %}{{ result.watchlist_item|tojson|forceescape }}{% endif %}'><svg class="ui-icon" aria-hidden="true"><use href="#icon-star"/></svg><span class="favorite-text">收藏当前标的</span></button></div>
      <div class="workspace-grid">
        <div>
          <div class="metric-selector" id="metric-picker">
            <button class="metric-option active" type="button"><svg class="ui-icon"><use href="#icon-chart"/></svg>估值</button>
            <button class="metric-option" type="button">一把手：市盈率</button>
            <button class="metric-option" type="button">二把手：市净率</button>
            <button class="metric-option" type="button">股息率</button>
            <button class="metric-option" type="button">ROE</button>
          </div>
          <div class="valuation-table" id="valuation-data">
            <div class="valuation-row head"><span>指标</span><span>当前值</span><span>参考</span><span>状态</span></div>
            {% if result %}
              {% for row in result.summary.buy_rows[:6] %}
              <div class="valuation-row"><span>{{ row.label }}</span><span>{{ row.value }}</span><span>{{ row.note }}</span><span class="pos">已更新</span></div>
              {% endfor %}
            {% else %}
            <div class="valuation-row"><span>当前值</span><span>-</span><span>搜索后展示</span><span>等待数据</span></div>
            <div class="valuation-row"><span>20日均线</span><span>-</span><span>搜索后展示</span><span>等待数据</span></div>
            <div class="valuation-row"><span>RSI</span><span>-</span><span>搜索后展示</span><span>等待数据</span></div>
            {% endif %}
          </div>
        </div>
        <div>
          <div class="secondary-metric">{{ result.symbol if result else '搜索标的' }} · {{ result.unit_label if result else '当前值' }}</div>
          <div class="secondary-note">{% if result %}{{ result.summary.signal_text }}{% else %}搜索基金、股票或指数代码后，这里会展示当前值、风险位置、指标温度和本次重绘的走势图。{% endif %}</div>
        </div>
      </div>
      <div class="backtest-header">
        <div class="backtest-heading"><svg class="ui-icon"><use href="#icon-history"/></svg>以上指标的历史回测</div>
        <div class="backtest-scales" aria-label="回测时间尺度">
          <button class="backtest-scale" type="button" data-time-scale="1y" onclick="window.applyBacktestScale?.('1y')">近1年</button>
          <button class="backtest-scale" type="button" data-time-scale="3y" onclick="window.applyBacktestScale?.('3y')">近3年</button>
          <button class="backtest-scale" type="button" data-time-scale="5y" onclick="window.applyBacktestScale?.('5y')">近5年</button>
          <button class="backtest-scale active" type="button" data-time-scale="all" onclick="window.applyBacktestScale?.('all')">全部</button>
        </div>
      </div>
      <div class="workspace-chart" id="workspace-backtest" data-backtest-chart>
        <script type="application/json" class="backtest-equity-data">{{ result.equity_points|tojson if result else '[]' }}</script>
        <script type="application/json" class="backtest-benchmark-data">{{ result.benchmark_points|tojson if result else '[]' }}</script>
        <script type="application/json" class="backtest-history-data">{{ result.history_points|tojson if result else '[]' }}</script>
        <svg viewBox="0 0 980 360" role="img" aria-labelledby="backtest-chart-title backtest-chart-desc">
          <title id="backtest-chart-title">指标历史回测图</title>
          <desc id="backtest-chart-desc">基于当前项目回测结果绘制策略、买入持有和回撤曲线。</desc>
        </svg>
        <div class="workspace-chart-legend"><span><i></i>策略回测</span><span><i></i>买入持有</span><span><i></i>回撤</span></div>
        <div class="history-chart-empty" id="workspace-backtest-empty" hidden>暂无可用回测数据。</div>
      </div>
    </section>
    <section class="sell-workspace" id="sell-workspace" data-workspace-view hidden>
      <header class="sell-head"><h1>风控提醒</h1><p>这里记录离场和降风险的复盘口径，不自动生成交易指令。</p></header>
      <div class="sell-strategy-grid" aria-label="卖出策略类型">
        <button class="sell-card active" type="button" data-sell-strategy="profit" onclick="window.applySellStrategy?.('profit')"><h2>按盈利百分比卖</h2><p>达到目标收益后分批止盈，适合有明确收益目标的定投或波段计划。</p></button>
        <button class="sell-card" type="button" data-sell-strategy="valuation" onclick="window.applySellStrategy?.('valuation')"><h2>按估值卖</h2><p>估值进入高位或分位过热时减仓，适合指数基金和估值驱动品种。</p></button>
        <button class="sell-card" type="button" data-sell-strategy="hold" onclick="window.applySellStrategy?.('hold')"><h2>不卖</h2><p>长期持有，只记录风险和再平衡提醒，不因为短期波动触发卖出。</p></button>
        <button class="sell-card" type="button" data-sell-strategy="custom" onclick="window.applySellStrategy?.('custom')"><h2>自定义策略</h2><p>组合收益、估值、回撤、持仓比例等条件，形成自己的透明规则。</p></button>
      </div>
      <div class="sell-rule-panel">
        <h2>策略参数</h2>
        <div class="sell-rule-grid">
          <div class="sell-rule-field"><label for="profitTarget">目标收益</label><input id="profitTarget" value="30%" aria-label="目标收益"></div>
          <div class="sell-rule-field"><label for="valuationLimit">估值阈值</label><select id="valuationLimit"><option>估值分位高于 80%</option><option>估值分位高于 90%</option><option>PE 高于历史中位</option></select></div>
          <div class="sell-rule-field"><label for="sellAction">处理方式</label><select id="sellAction"><option>提醒复核</option><option>分批减仓提醒</option><option>仅记录不提醒</option></select></div>
          <div class="sell-rule-field full"><label for="customSellRule">自定义规则</label><textarea id="customSellRule" placeholder="例如：盈利超过 40% 且估值分位高于 85% 时，提示分三次复核卖出。"></textarea></div>
        </div>
      </div>
    </section>
    <section class="agent-workspace" id="agent-workspace" data-workspace-view hidden>
      <header class="agent-workspace-head"><h1>智能体搭建</h1><p>定义分析目标、数据边界和判断规则，所有结论保留依据与计算口径。</p></header>
      <div class="agent-builder-grid">
        <form class="agent-builder" id="agentBuilderForm">
          <div class="agent-form-grid">
            <div class="agent-field"><label for="agentName">智能体名称</label><input id="agentName" value="估值观察智能体"></div>
            <div class="agent-field"><label for="agentFrequency">运行频率</label><select id="agentFrequency"><option>手动运行</option><option>每日收盘后</option><option>每周一</option></select></div>
            <div class="agent-field full"><label for="agentGoal">主要任务</label><textarea id="agentGoal">评估收藏标的的估值水平，解释低估、正常或高估的依据，并给出需要持续观察的数据变化。</textarea></div>
            <div class="agent-field full"><label>允许使用的数据</label><div class="agent-options"><label><input type="checkbox" checked>公开行情</label><label><input type="checkbox" checked>财务指标</label><label><input type="checkbox" checked>历史分位</label><label><input type="checkbox">用户持仓</label></div></div>
            <div class="agent-field"><label for="agentRule">评估规则</label><select id="agentRule"><option>通用公开规则</option><option>我的自定义规则</option></select></div>
            <div class="agent-field"><label for="agentOutput">输出方式</label><select id="agentOutput"><option>结论 + 数据依据</option><option>仅异常提醒</option><option>完整分析报告</option></select></div>
            <div class="agent-field full"><label for="agentGuardrail">约束与边界</label><textarea id="agentGuardrail">不生成买卖指令；缺失数据明确留空；每项结论显示数据来源、更新时间和命中的规则。</textarea></div>
          </div>
          <div class="agent-actions"><button type="submit">创建智能体</button><span class="agent-build-feedback" id="agentBuildFeedback"></span></div>
        </form>
        <aside class="agent-preview" aria-label="智能体配置预览">
          <h2>运行配置</h2>
          <ul class="agent-preview-list"><li><span>状态</span><strong id="agentPreviewStatus">草稿</strong></li><li><span>对象</span><strong>我的收藏</strong></li><li><span>规则</span><strong id="agentPreviewRule">通用公开规则</strong></li><li><span>输出</span><strong id="agentPreviewOutput">结论 + 数据依据</strong></li><li><span>执行</span><strong id="agentPreviewFrequency">手动运行</strong></li></ul>
          <p class="agent-transparency">透明度要求：展示数据源、更新时间、计算公式、命中规则及无法判断的原因。</p>
          <div class="created-agent-panel" aria-label="已创建智能体">
            <div class="created-agent-head"><h3>已创建智能体</h3><span id="createdAgentCount">0 个</span></div>
            <div class="created-agent-list" id="createdAgentList"><div class="created-agent-empty">还没有创建智能体</div></div>
            <button class="created-agent-build" id="startAgentBuild" type="button">搭建智能体</button>
          </div>
        </aside>
      </div>
    </section>
    <section class="account-workspace" id="account-workspace" data-workspace-view hidden>
      <div class="account-card">
        <div class="account-avatar" aria-hidden="true">我</div>
        <div class="account-info">
          <span>个人账号</span>
          <strong>guest</strong>
        </div>
      </div>
    </section>
    <section class="plan-workspace" id="plan-workspace" data-workspace-view hidden>
      <header class="plan-head">
        <p class="plan-quote">“凡事预则立，不预则废。”</p>
        <h1>计划</h1>
        <p>这里留给用户自己写计划。可以直接套模板，也可以完全按自己的方式整理。</p>
      </header>
      <div class="plan-panel">
        <div class="plan-mode-row" aria-label="计划模式">
          <button type="button" class="plan-mode-button active" data-plan-mode="template">模板</button>
          <button type="button" class="plan-mode-button" data-plan-mode="custom">自定义</button>
        </div>
        <div class="plan-template-box" id="planTemplateBox">今日目标：
1. 
2. 
3. 

执行步骤：
1. 
2. 
3. 

风险与阻塞：
1. 
2. 

完成标准：
1. 
2. </div>
        <textarea id="planEditor" class="plan-editor" placeholder="在这里输入你自己的计划内容..."></textarea>
        <div class="plan-meta" id="planMeta">本地自动保存，刷新后仍会保留。</div>
      </div>
    </section>
  </main>
  <div class="submit-overlay" id="submitOverlay"><div class="submit-card"><div class="spinner"></div><strong>正在分析</strong><small id="submitOverlayHint">正在拉取行情、计算指标和生成图表，通常需要 5-15 秒。</small></div></div>
  <nav class="top-nav">
    <div class="brand-lockup"><span class="menu-mark">☰</span><span class="brand-mark">♜</span></div>
    <div class="report-title"><h1>{% if result and result.market == 'fund' %}基金复盘报告{% elif result and result.market == 'a_stock' %}股票复盘报告{% elif result and result.market == 'crypto' %}数字资产复盘报告{% elif result %}标的复盘报告{% else %}复盘工作台{% endif %}<small>v2.0.5</small></h1></div>
    <div class="nav-actions"><span>报告生成时间：{{ result.generated_at if result and result.generated_at else "2025-05-24 15:30:21" }}</span><button type="button" class="auth-btn ghost js-save-report">保存</button><a class="auth-btn ghost" href="#result-panel">标准报告</a></div>
  </nav>
  <div class="shell">
    <section class="layout">
      <div class="stack">
        <aside class="left-rail">
        <div class="panel" id="direct-panel"><div class="panel-head"><div><h2 class="section-title" style="margin:0;">标的参数</h2></div></div><form method="post"><input type="hidden" name="mode" value="analyze"><div class="field"><label for="symbol">标的代码</label><input id="symbol" name="symbol" value="{{ form.symbol }}" placeholder="000300.SH"></div><div class="field"><label for="market">市场</label><select id="market" name="market">{% for item in ['fund','a_stock','us_stock','crypto'] %}<option value="{{ item }}" {% if form.market == item %}selected{% endif %}>{{ {'fund':'基金','a_stock':'A股','us_stock':'美股','crypto':'数字资产'}[item] }}</option>{% endfor %}</select></div><div class="field"><label>基准指数</label><input value="{{ default_symbol }}" placeholder="000300.SH"></div><div class="field"><label for="period">回测区间</label><div class="row-2"><input id="start_date" name="start_date" type="date" value="{{ form.start_date }}"><input id="end_date" name="end_date" type="date" value="{{ form.end_date }}"></div><div class="range-buttons"><button type="button" data-period="1y" data-years="1">近1年</button><button type="button" data-period="3y" data-years="3">近3年</button><button type="button" data-period="5y" data-years="5">近5年</button><button type="button" data-period="max" class="primary">全部</button></div><select id="period" name="period" style="margin-top:8px;">{% for item in ['1mo','3mo','6mo','1y','2y','3y','5y','10y','20y','50y','max'] %}<option value="{{ item }}" {% if form.period == item %}selected{% endif %}>{{ item }}</option>{% endfor %}</select></div><div class="field"><label>交易频率</label><select><option>日频</option><option>周频</option><option>月频</option></select></div><div class="field"><label for="use_ai">AI 分析深度</label><select id="use_ai" name="use_ai"><option value="false" {% if not form.use_ai %}selected{% endif %}>标准</option><option value="true" {% if form.use_ai %}selected{% endif %}>全面</option></select></div><div class="toggle-row"><label>自动刷新数据 <span class="switch on"></span></label><label>包含未上市数据 <span class="switch"></span></label><label>使用最新财报 <span class="switch on"></span></label></div><div class="actions" style="margin-top:12px;"><button class="primary" type="submit" style="width:100%;">刷新数据</button></div></form></div>
          <div class="panel" id="agent-panel"><div class="panel-head"><div><h2>追问报告</h2></div><div class="panel-tag">Agent</div></div><form method="post"><input type="hidden" name="mode" value="chat"><div class="field"><label for="prompt">你的请求</label><textarea id="prompt" name="prompt" placeholder="输入追问">{{ form.prompt }}</textarea></div><div class="actions"><button class="primary" type="submit">发送给 Agent</button></div></form><div class="chip-row" style="margin-top:10px;"><span class="chip" data-prompt="分析 002982 基金，生成标准报告">标准报告</span><span class="chip" data-prompt="把报告改写成老板速读版">老板速读版</span><span class="chip" data-prompt="补充风险提示和异常解释">补充风险</span></div></div>
          <div class="data-card"><strong>数据状态</strong><div class="data-row"><span>数据来源：</span><span>公共行情接口</span></div><div class="data-row"><span>生成时间：</span><span>{{ result.generated_at if result else '-' }} <i class="dot-ok"></i></span></div><div class="data-row"><span>数据区间：</span><span>{{ result.data_range if result else '搜索后显示' }}</span></div></div><div class="muted" style="margin-top:22px;">报告用于复盘和投教，不构成投资建议。</div>
        </aside>
      </div>
      <main class="report-main">
        <div class="panel result-panel" id="result-panel">{% if error %}<div class="notice error">{{ error }}</div>{% endif %}{% if note %}<div class="notice">{{ note }}</div>{% endif %}
          {% if result %}
          <div class="section-title">复盘结果</div>
          <div class="kpis">
            <div class="kpi"><span>标的</span><strong>{{ result.symbol }}</strong></div>
            <div class="kpi"><span>{{ result.unit_label }}</span><strong>{{ result.latest_price or '-' }}</strong></div>
            <div class="kpi"><span>日变化</span><strong>{{ result.summary.change_pct }}</strong></div>
            <div class="kpi"><span>数据条数</span><strong>{{ result.data_points }}</strong></div>
            <div class="kpi"><span>20日均线</span><strong>{{ result.summary.ma20 }}</strong></div>
            <div class="kpi"><span>RSI</span><strong>{{ result.summary.rsi }}</strong></div>
          </div>
          <div class="evidence-note">{{ result.summary.evidence_note }}</div>
          <div class="report-grid-2">
            <section class="buy-data-table" aria-label="复盘证据">
              <h3>复盘证据</h3>
              <div class="buy-metric-strip" role="list">{% for row in result.summary.buy_rows %}<div class="buy-metric" role="listitem" data-metric-key="{{ row.label }}" draggable="true" tabindex="0"><span>{{ row.label }}</span><strong>{{ row.value }}</strong><small>{{ row.note }}</small></div>{% endfor %}</div>
            </section>
            <section class="history-chart-panel" aria-label="实时复盘图">
              <div class="history-chart-head">
                <h3>实时复盘图</h3>
                <div class="history-range-tabs" aria-label="历史走势图时间范围">
                  <button type="button" class="active" data-history-range="live">最新</button>
                  <button type="button" data-history-range="1m">一个月</button>
                  <button type="button" data-history-range="1y">一年</button>
                  <button type="button" data-history-range="10y">十年</button>
                  <button type="button" data-history-range="all">至今</button>
                </div>
              </div>
              <script type="application/json" class="history-chart-data">{{ result.history_points|tojson }}</script>
              <div class="split-chart-stack" data-split-history-chart>
                <div class="chart-board price-chart"><div class="chart-board-title"><span>{{ result.unit_label }} / 均线</span><div class="inline-chart-legend" aria-label="价格图图例"><span><i></i>价格/净值</span><span class="ma20"><i></i>MA20</span><span class="ma60"><i></i>MA60</span></div></div><svg viewBox="0 0 980 390" role="img" aria-label="{{ result.symbol }} 价格走势图"></svg></div>
                <div class="chart-board indicator-chart"><div class="chart-board-title"><span>RSI</span><div class="inline-chart-legend" aria-label="RSI 图例"><span class="rsi"><i></i>RSI</span><span class="rsi-high"><i></i>70</span><span class="rsi-low"><i></i>30</span></div></div><svg viewBox="0 0 980 170" role="img" aria-label="{{ result.symbol }} RSI 指标图"></svg></div>
              </div>
              <div class="chart-legend"><span><i></i>价格/净值</span><span><i></i>MA20</span><span><i></i>MA60</span></div>
            </section>
          </div>
          <div class="section-title">分析日志</div>
          <div class="report-box">{{ result.log }}</div>
          {% endif %}
          <div class="section-title">复盘追问</div>
          <div class="agent-card" id="agent-tools" data-followup-card><div><strong>把结论说清楚</strong><span class="muted" data-followup-context>优先解释回撤、数据新鲜度、指标是否过热，以及哪些结论还需要人工复核。</span></div><button type="button" class="chip followup-toggle">继续问</button><div class="followup-box"><textarea class="followup-question" rows="3" placeholder="例如：这只基金现在最大的问题是什么？"></textarea><div class="actions"><button type="button" class="primary followup-send">发送</button></div><div class="followup-output"></div></div></div>
        </div>
      </main>
      <aside class="right-rail">
        <section style="margin-top:18px;"><div class="panel-head"><div><h2>导出与分享</h2></div></div><div class="export-list"><button type="button" class="js-save-report primary">保存报告配置</button><button type="button" class="js-share-report">分享报告链接</button></div><div class="action-feedback" id="reportActionFeedback" hidden></div></section>
      </aside>
    </section>
  </div>
  <script>
    const brokerDataReady = {{ 'true' if broker_data_ready else 'false' }};
    const brokerDataSourceLabel = {{ broker_data_source_label|tojson }};
    const brokerMissingMessage = `${brokerDataSourceLabel}，无法展示券商行情图。配置券商行情接口后，本区域才会绘制真实数据。`;
    const brokerEmptyPanelHtml = (message = brokerMissingMessage) => `
      <div class="broker-empty-panel">
        <strong>券商行情未接入</strong>
        <span>${message}</span>
        <span>请在环境变量中配置 <code>BROKER_PROVIDER</code>、<code>BROKER_API_URL</code>、<code>BROKER_API_KEY</code> 后重启项目。</span>
        <div class="broker-status-line" data-broker-status-line>正在检查券商连接状态...</div>
      </div>`;
    const refreshBrokerStatusText = async () => {
      const nodes = document.querySelectorAll('[data-broker-status-line]');
      if (!nodes.length) return;
      try {
        const res = await fetch('{{ url_for("broker_status_api") }}');
        const data = await res.json();
        const text = data.connected ? `${data.provider} 已连接` : (data.message || '券商 API 未连接');
        nodes.forEach(node => { node.textContent = text; });
      } catch (_) {
        nodes.forEach(node => { node.textContent = '券商状态接口不可用'; });
      }
    };
    const renderSplitHistoryCharts = () => {
      const ranges = {
        live: { label:'实时', points:10 },
        '1m': { label:'一个月', days:31 },
        '1y': { label:'一年', days:365 },
        '10y': { label:'十年', days:3650 },
        all: { label:'至今' }
      };
      const parseDate = value => {
        const parts = String(value || '').split('-').map(Number);
        return parts.length === 3 ? new Date(parts[0], parts[1] - 1, parts[2]) : null;
      };
      const filterPoints = (points, key) => {
        const valid = points.filter(point => point && point.date && Number.isFinite(Number(point.close)));
        if (!valid.length) return [];
        if (key === 'live') return valid.slice(-ranges.live.points);
        if (key === 'all') return valid;
        const lastDate = parseDate(valid[valid.length - 1].date);
        if (!lastDate) return valid;
        const cutoff = new Date(lastDate);
        cutoff.setDate(cutoff.getDate() - (ranges[key]?.days || 365));
        const scoped = valid.filter(point => {
          const date = parseDate(point.date);
          return date && date >= cutoff;
        });
        return scoped.length ? scoped : valid.slice(-Math.min(valid.length, 20));
      };
      const pathFor = (points, key, xFor, yFor) => {
        const coords = points
          .map((point, index) => ({ x:xFor(index), y:yFor(point[key]), value:point[key] }))
          .filter(item => Number.isFinite(Number(item.value)) && Number.isFinite(item.x) && Number.isFinite(item.y));
        if (!coords.length) return '';
        if (coords.length < 3) return coords.map((item, index) => `${index ? 'L' : 'M'}${item.x.toFixed(1)} ${item.y.toFixed(1)}`).join(' ');
        let path = `M${coords[0].x.toFixed(1)} ${coords[0].y.toFixed(1)}`;
        for (let index = 0; index < coords.length - 1; index += 1) {
          const p0 = coords[Math.max(0, index - 1)];
          const p1 = coords[index];
          const p2 = coords[index + 1];
          const p3 = coords[Math.min(coords.length - 1, index + 2)];
          const cp1x = p1.x + (p2.x - p0.x) / 6;
          const cp1y = p1.y + (p2.y - p0.y) / 6;
          const cp2x = p2.x - (p3.x - p1.x) / 6;
          const cp2y = p2.y - (p3.y - p1.y) / 6;
          path += ` C${cp1x.toFixed(1)} ${cp1y.toFixed(1)} ${cp2x.toFixed(1)} ${cp2y.toFixed(1)} ${p2.x.toFixed(1)} ${p2.y.toFixed(1)}`;
        }
        return path;
      };
      const drawGrid = (width, height, left, right, top, bottom, yLabels, xLabels) => {
        const chartW = width - left - right;
        const chartH = height - top - bottom;
        const rows = yLabels.length - 1;
        const cols = Math.max(1, xLabels.length - 1);
        let grid = `<rect width="${width}" height="${height}" fill="#fff"/>`;
        for (let i = 0; i <= rows; i += 1) {
          const y = top + (chartH * i / rows);
          grid += `<path d="M${left} ${y.toFixed(1)}H${width - right}" stroke="#edf1f5"/>`;
          grid += `<text x="${left - 8}" y="${(y + 4).toFixed(1)}" text-anchor="end" fill="#667085" font-size="11">${yLabels[i]}</text>`;
        }
        for (let i = 0; i <= cols; i += 1) {
          const x = left + (chartW * i / cols);
          grid += `<path d="M${x.toFixed(1)} ${top}V${height - bottom}" stroke="#f2f5f8"/>`;
        }
        xLabels.forEach((label, index) => {
          const x = left + (chartW * index / Math.max(1, xLabels.length - 1));
          grid += `<text x="${x.toFixed(1)}" y="${height - 12}" text-anchor="middle" fill="#667085" font-size="11">${label}</text>`;
        });
        grid += `<path d="M${left} ${top}V${height - bottom}H${width - right}" stroke="#98a2b3" fill="none"/>`;
        return grid;
      };
      const formatNumber = value => {
        const number = Number(value);
        if (!Number.isFinite(number)) return '-';
        return number >= 100 ? number.toFixed(1) : number.toFixed(4);
      };
      const escapeSvgText = value => String(value ?? '').replace(/[&<>"']/g, char => ({
        '&':'&amp;',
        '<':'&lt;',
        '>':'&gt;',
        '"':'&quot;',
        "'":'&#39;'
      }[char]));
      const renderPriceSelection = (svg, state, index) => {
        if (!svg || !state || !state.scoped.length) return;
        const safeIndex = Math.max(0, Math.min(state.scoped.length - 1, index));
        const point = state.scoped[safeIndex];
        const x = state.xFor(safeIndex);
        const y = state.priceY(point.close);
        if (!Number.isFinite(x) || !Number.isFinite(y)) return;
        const label = `X: ${point.date}  Y: ${formatNumber(point.close)}`;
        const labelWidth = Math.max(154, Math.min(265, label.length * 7.2 + 18));
        const labelX = Math.min(Math.max(x + 12, state.left), state.width - state.right - labelWidth);
        const labelY = Math.max(state.top + 8, y - 38);
        const overlay = [
          `<g class="chart-selection" aria-hidden="true">`,
          `<path class="chart-crosshair-line" d="M${x.toFixed(1)} ${state.top}V${state.priceHeight - state.bottom}"/>`,
          `<path class="chart-crosshair-line" d="M${state.left} ${y.toFixed(1)}H${state.width - state.right}"/>`,
          `<circle class="chart-crosshair-point" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="5"/>`,
          `<g class="chart-crosshair-label">`,
          `<rect x="${labelX.toFixed(1)}" y="${labelY.toFixed(1)}" width="${labelWidth.toFixed(1)}" height="27" rx="6" fill="#172033" opacity=".92"/>`,
          `<text x="${(labelX + 9).toFixed(1)}" y="${(labelY + 18).toFixed(1)}" fill="#fff" font-size="12" font-weight="700">${escapeSvgText(label)}</text>`,
          `</g>`,
          `</g>`
        ].join('');
        svg.querySelector('.chart-selection')?.remove();
        svg.insertAdjacentHTML('beforeend', overlay);
        svg.setAttribute('aria-label', `${svg.dataset.baseLabel || svg.getAttribute('aria-label') || ''} ${label}`.trim());
      };
      const bindPriceChartEvents = svg => {
        if (!svg || svg.__priceChartEventsBound) return;
        svg.__priceChartEventsBound = true;
        svg.addEventListener('click', event => {
          const state = svg.__priceChartState;
          if (!state || !state.scoped.length) return;
          const point = svg.createSVGPoint();
          point.x = event.clientX;
          point.y = event.clientY;
          const matrix = svg.getScreenCTM();
          if (!matrix) return;
          const local = point.matrixTransform(matrix.inverse());
          const ratio = (local.x - state.left) / Math.max(1, state.chartW);
          const index = Math.round(ratio * Math.max(0, state.scoped.length - 1));
          svg.__selectedPriceIndex = Math.max(0, Math.min(state.scoped.length - 1, index));
          renderPriceSelection(svg, state, svg.__selectedPriceIndex);
        });
        svg.addEventListener('keydown', event => {
          if (!['ArrowLeft','ArrowRight','Home','End'].includes(event.key)) return;
          const state = svg.__priceChartState;
          if (!state || !state.scoped.length) return;
          event.preventDefault();
          const current = Number.isInteger(svg.__selectedPriceIndex) ? svg.__selectedPriceIndex : state.scoped.length - 1;
          if (event.key === 'Home') svg.__selectedPriceIndex = 0;
          else if (event.key === 'End') svg.__selectedPriceIndex = state.scoped.length - 1;
          else svg.__selectedPriceIndex = Math.max(0, Math.min(state.scoped.length - 1, current + (event.key === 'ArrowRight' ? 1 : -1)));
          renderPriceSelection(svg, state, svg.__selectedPriceIndex);
        });
      };
      const renderPanel = (panel, key = 'live') => {
        const dataNode = panel.querySelector('.history-chart-data');
        const chartNode = panel.querySelector('[data-split-history-chart]');
        const priceSvg = panel.querySelector('.price-chart svg');
        const rsiSvg = panel.querySelector('.indicator-chart svg');
        let points = [];
        try { points = JSON.parse(dataNode?.textContent || '[]'); } catch (_) { points = []; }
        const scoped = filterPoints(points, key);
        if (!scoped.length) {
          if (chartNode) chartNode.innerHTML = '<div class="chart-empty">暂无可用历史数据。</div>';
          return;
        }
        const priceValues = scoped.flatMap(point => [point.close, point.ma20, point.ma60].filter(value => Number.isFinite(Number(value))).map(Number));
        const minPrice = Math.min(...priceValues);
        const maxPrice = Math.max(...priceValues);
        const pricePad = Math.max((maxPrice - minPrice) * 0.08, Math.abs(maxPrice || 1) * 0.01);
        const yMin = minPrice - pricePad;
        const yMax = maxPrice + pricePad;
        const width = 980, priceHeight = 390, rsiHeight = 170;
        const left = 64, right = 24, top = 24, bottom = 42;
        const chartW = width - left - right;
        const priceChartH = priceHeight - top - bottom;
        const rsiChartH = rsiHeight - top - bottom;
        const xFor = index => left + (chartW * index / Math.max(1, scoped.length - 1));
        const priceY = value => {
          const number = Number(value);
          return priceHeight - bottom - ((number - yMin) / Math.max(0.000001, yMax - yMin)) * priceChartH;
        };
        const rsiY = value => {
          const number = Number(value);
          return rsiHeight - bottom - ((number - 0) / 100) * rsiChartH;
        };
        const labels = scoped.length <= 1 ? [scoped[0].date] : [
          scoped[0].date,
          scoped[Math.floor(scoped.length / 2)].date,
          scoped[scoped.length - 1].date
        ];
        const priceLabels = [formatNumber(yMax), formatNumber((yMax + yMin) / 2), formatNumber(yMin)];
        const pricePath = pathFor(scoped, 'close', xFor, priceY);
        const ma20Path = pathFor(scoped, 'ma20', xFor, priceY);
        const ma60Path = pathFor(scoped, 'ma60', xFor, priceY);
        const lastPoint = scoped[scoped.length - 1];
        if (priceSvg && !priceSvg.dataset.baseLabel) priceSvg.dataset.baseLabel = priceSvg.getAttribute('aria-label') || '';
        priceSvg.innerHTML = [
          drawGrid(width, priceHeight, left, right, top, bottom, priceLabels, labels),
          `<path d="${pricePath}" fill="none" stroke="#1d4ed8" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>`,
          ma20Path ? `<path d="${ma20Path}" fill="none" stroke="#f59e0b" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>` : '',
          ma60Path ? `<path d="${ma60Path}" fill="none" stroke="#16a34a" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>` : '',
          `<rect class="chart-hit-layer" x="${left}" y="${top}" width="${chartW}" height="${priceChartH}" tabindex="0"/>`,
          `<text x="${width - right}" y="18" text-anchor="end" fill="#172033" font-size="12" font-weight="700">${ranges[key]?.label || '至今'} · ${lastPoint.date} · ${formatNumber(lastPoint.close)}</text>`
        ].join('');
        priceSvg.tabIndex = 0;
        priceSvg.__priceChartState = { scoped, xFor, priceY, width, priceHeight, left, right, top, bottom, chartW };
        bindPriceChartEvents(priceSvg);
        if (Number.isInteger(priceSvg.__selectedPriceIndex)) {
          renderPriceSelection(priceSvg, priceSvg.__priceChartState, priceSvg.__selectedPriceIndex);
        }
        const rsiPath = pathFor(scoped, 'rsi', xFor, rsiY);
        rsiSvg.innerHTML = [
          drawGrid(width, rsiHeight, left, right, top, bottom, ['100','50','0'], labels),
          `<path d="M${left} ${rsiY(70).toFixed(1)}H${width - right}" stroke="#ef4444" stroke-dasharray="6 5"/>`,
          `<path d="M${left} ${rsiY(30).toFixed(1)}H${width - right}" stroke="#22c55e" stroke-dasharray="6 5"/>`,
          rsiPath ? `<path d="${rsiPath}" fill="none" stroke="#8b5cf6" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>` : `<text x="${width / 2}" y="${rsiHeight / 2}" text-anchor="middle" fill="#667085" font-size="13">当前时间范围 RSI 数据不足</text>`
        ].join('');
      };
      document.querySelectorAll('.history-chart-panel').forEach(panel => {
        renderPanel(panel, 'live');
        panel.querySelectorAll('[data-history-range]').forEach(button => {
          button.addEventListener('click', () => {
            panel.querySelectorAll('[data-history-range]').forEach(item => item.classList.toggle('active', item === button));
            renderPanel(panel, button.dataset.historyRange || 'live');
          });
        });
      });
    };
    renderSplitHistoryCharts();
    const buyMetricOrderStorageKey = 'quant-buy-metric-order-v1';
    const readBuyMetricOrder = () => {
      try {
        const parsed = JSON.parse(localStorage.getItem(buyMetricOrderStorageKey) || '[]');
        return Array.isArray(parsed) ? parsed : [];
      } catch (_) {
        return [];
      }
    };
    const writeBuyMetricOrder = strip => {
      const order = Array.from(strip.querySelectorAll('.buy-metric')).map(card => card.dataset.metricKey || card.textContent.trim());
      try { localStorage.setItem(buyMetricOrderStorageKey, JSON.stringify(order)); } catch (_) { /* 排序只在当前页面生效 */ }
    };
    const applyBuyMetricOrder = strip => {
      const order = readBuyMetricOrder();
      if (!order.length) return;
      const rank = new Map(order.map((key, index) => [key, index]));
      Array.from(strip.querySelectorAll('.buy-metric'))
        .sort((left, right) => {
          const leftRank = rank.has(left.dataset.metricKey) ? rank.get(left.dataset.metricKey) : Number.MAX_SAFE_INTEGER;
          const rightRank = rank.has(right.dataset.metricKey) ? rank.get(right.dataset.metricKey) : Number.MAX_SAFE_INTEGER;
          return leftRank - rightRank;
        })
        .forEach(card => strip.append(card));
    };
    const metricAfterPointer = (strip, x) => {
      return Array.from(strip.querySelectorAll('.buy-metric:not(.dragging)')).reduce((closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = x - box.left - box.width / 2;
        return offset < 0 && offset > closest.offset ? { offset, element:child } : closest;
      }, { offset:Number.NEGATIVE_INFINITY, element:null }).element;
    };
    const initBuyMetricSorting = () => {
      document.querySelectorAll('.buy-metric-strip').forEach(strip => {
        applyBuyMetricOrder(strip);
        strip.querySelectorAll('.buy-metric').forEach(card => {
          card.addEventListener('dragstart', event => {
            card.classList.add('dragging');
            event.dataTransfer?.setData('text/plain', card.dataset.metricKey || '');
            if (event.dataTransfer) event.dataTransfer.effectAllowed = 'move';
          });
          card.addEventListener('dragend', () => {
            card.classList.remove('dragging');
            strip.querySelectorAll('.drop-before').forEach(item => item.classList.remove('drop-before'));
            writeBuyMetricOrder(strip);
          });
          card.addEventListener('keydown', event => {
            if (!['ArrowLeft','ArrowRight'].includes(event.key)) return;
            event.preventDefault();
            if (event.key === 'ArrowLeft' && card.previousElementSibling) strip.insertBefore(card, card.previousElementSibling);
            if (event.key === 'ArrowRight' && card.nextElementSibling) strip.insertBefore(card.nextElementSibling, card);
            card.focus();
            writeBuyMetricOrder(strip);
          });
        });
        strip.addEventListener('dragover', event => {
          event.preventDefault();
          const dragging = strip.querySelector('.buy-metric.dragging');
          if (!dragging) return;
          const after = metricAfterPointer(strip, event.clientX);
          strip.querySelectorAll('.drop-before').forEach(item => item.classList.remove('drop-before'));
          if (after) {
            after.classList.add('drop-before');
            strip.insertBefore(dragging, after);
          } else {
            strip.append(dragging);
          }
        });
        strip.addEventListener('drop', event => {
          event.preventDefault();
          strip.querySelectorAll('.drop-before').forEach(item => item.classList.remove('drop-before'));
          writeBuyMetricOrder(strip);
        });
      });
    };
    initBuyMetricSorting();
    const valuationRule = document.getElementById('valuationRule');
    const refreshValuationButton = document.getElementById('refreshValuation');
    const customRuleEditor = document.querySelector('.custom-rule-editor');
    const ruleFeedback = document.getElementById('ruleFeedback');
    valuationRule?.addEventListener('click', () => {
      document.querySelector('.rule-disclosure')?.setAttribute('open', '');
    });
    valuationRule?.addEventListener('change', () => {
      customRuleEditor?.classList.toggle('active', valuationRule.value === 'custom');
      document.querySelector('.rule-disclosure')?.setAttribute('open', '');
      if (ruleFeedback) ruleFeedback.textContent = '';
    });
    document.getElementById('saveCustomRule')?.addEventListener('click', () => {
      const rule = document.getElementById('customRuleText')?.value.trim();
      if (ruleFeedback) ruleFeedback.textContent = rule ? '规则已保存，后续评估将采用该口径。' : '请先输入自定义规则。';
    });
    refreshValuationButton?.addEventListener('click', () => {
      if (ruleFeedback) ruleFeedback.textContent = valuationRule?.value === 'custom' ? '正在按自定义口径刷新...' : '正在按通用复盘口径刷新...';
      document.querySelector('.rule-disclosure')?.setAttribute('open', '');
      refreshWatchlistRealtime();
    });
    const watchlistStorageKey = 'quant-watchlist-v1';
    const watchlistBody = document.getElementById('watchlistBody');
    const watchlistEmpty = document.getElementById('watchlistEmpty');
    const watchlistHeader = document.getElementById('watchlistHeader');
    const favoriteButtons = Array.from(document.querySelectorAll('[data-favorite-toggle]'));
    let watchlistMemory = [];
    let watchlistStorageUsable = true;
    const knownSecurityNames = { '000300':'沪深300', '000905':'中证500', '000016':'上证50', '000852':'中证1000', '270048':'广发纯债债券A', '006479':'广发纳斯达克100ETF联接人民币(QDII)C' };
    const normalizeWatchlistSymbol = symbol => String(symbol || '').trim().toUpperCase();
    const parseWatchlistPayload = button => {
      try {
        const payload = JSON.parse(button.dataset.watchlistItem || '{}');
        return payload && typeof payload === 'object' ? payload : {};
      } catch (_) {
        return {};
      }
    };
    const fallbackSecurityName = symbol => knownSecurityNames[normalizeWatchlistSymbol(symbol)] || symbol;
    const normalizeWatchlistItem = item => {
      const normalized = { ...item };
      normalized.symbol = normalizeWatchlistSymbol(normalized.symbol);
      normalized.name = normalized.name && normalized.name !== normalized.symbol ? normalized.name : fallbackSecurityName(normalized.symbol);
      const percentNumber = value => {
        const number = Number(String(value || '').replace('%', '').trim());
        return Number.isFinite(number) ? number : null;
      };
      const numericValue = value => {
        const number = Number(value);
        return Number.isFinite(number) ? number : null;
      };
      const inferMarketConclusion = entry => {
        const rsi = percentNumber(entry.rsi);
        const position = percentNumber(entry.position);
        const drawdown = percentNumber(entry.drawdown);
        const ma20 = numericValue(entry.ma20);
        const ma60 = numericValue(entry.ma60);
        if (rsi !== null && rsi <= 30) return ['接近超卖', 'status-high'];
        if (rsi !== null && rsi >= 70) return ['短线过热', 'status-high'];
        if (drawdown !== null && drawdown <= -10) return ['回撤较深', 'status-high'];
        if (position !== null && position >= 80 && drawdown !== null && drawdown < 0) return ['高位回撤', 'status-normal'];
        if (position !== null && position <= 20) return ['低位观察', 'status-low'];
        if (ma20 !== null && ma60 !== null && ma20 > ma60) return ['趋势偏强', 'status-low'];
        if (ma20 !== null && ma60 !== null && ma20 < ma60) return ['趋势偏弱', 'status-normal'];
        return ['待刷新', 'status-normal'];
      };
      const looksLikeLegacyMock = normalized.conclusion === '低估' && normalized.stars === '★★★★☆' && normalized.earningsYield === '8.01%' && normalized.pe === '12.48' && normalized.pb === '1.32' && normalized.dividend === '3.18%' && normalized.roe === '10.26%' && !normalized.valuationSource;
      if (looksLikeLegacyMock) {
        const [conclusion, status] = inferMarketConclusion(normalized);
        Object.assign(normalized, {
          status,
          conclusion,
          stars:'',
          earningsYield:'',
          pe:'',
          pb:'',
          dividend:'',
          roe:'',
          metricMode:'market',
          valuationSource:'legacy-cleared',
        });
      }
      if (normalized.conclusion === '行情观察') {
        const [conclusion, status] = inferMarketConclusion(normalized);
        normalized.conclusion = conclusion;
        normalized.status = status;
      }
      if (!normalized.conclusion) normalized.conclusion = '待刷新';
      if (!normalized.status) normalized.status = 'status-normal';
      return normalized;
    };
    const renderWatchlistHeader = items => {
      if (!watchlistHeader) return;
      const labels = ['关注标的','当前状态','最新值','市盈率','市净率','近一年位置','距高点','RSI','20日均线','60日均线','场内基金','场外基金'];
      watchlistHeader.replaceChildren(...labels.map(label => {
        const th = document.createElement('th');
        th.textContent = label;
        return th;
      }));
    };
    const readWatchlist = () => {
      if (watchlistMemory.length) return watchlistMemory.map(normalizeWatchlistItem);
      if (!watchlistStorageUsable) return watchlistMemory;
      try {
        const parsed = JSON.parse(localStorage.getItem(watchlistStorageKey) || '[]');
        return Array.isArray(parsed) ? parsed.map(normalizeWatchlistItem) : [];
      } catch (_) {
        return watchlistMemory;
      }
    };
    const writeWatchlist = items => {
      watchlistMemory = Array.isArray(items) ? items : [];
      try {
        const persisted = watchlistMemory.map(item => {
          const normalized = normalizeWatchlistItem(item);
          return {
            ...normalized,
            symbol: normalizeWatchlistSymbol(normalized.symbol),
            market: normalized.market || 'auto',
            name: normalized.name || fallbackSecurityName(normalized.symbol),
          };
        });
        localStorage.setItem(watchlistStorageKey, JSON.stringify(persisted));
        watchlistStorageUsable = true;
      } catch (_) {
        watchlistStorageUsable = false;
      }
    };
    let watchlistRealtimeInFlight = false;
    let watchlistRealtimeLoaded = false;
    const refreshWatchlistRealtime = async () => {
      if (watchlistRealtimeInFlight) return;
      const items = readWatchlist();
      if (!items.length) return;
      watchlistRealtimeInFlight = true;
      if (refreshValuationButton) refreshValuationButton.disabled = true;
      if (ruleFeedback) ruleFeedback.textContent = '正在实时获取远程行情...';
      try {
        const res = await fetch('{{ url_for("watchlist_realtime_api") }}', {
          method:'POST',
          headers:{ 'Content-Type':'application/json', 'X-CSRF-Token':'{{ csrf_token() }}' },
          body:JSON.stringify({ items:items.map(item => ({ symbol:item.symbol, market:item.market || 'auto', name:item.name })) })
        });
        const data = await res.json();
        if (!data.ok) throw new Error(data.error || '实时数据获取失败。');
        const remoteMap = new Map((data.items || []).map(item => [normalizeWatchlistSymbol(item.symbol), normalizeWatchlistItem(item)]));
        const merged = items.map(item => remoteMap.get(normalizeWatchlistSymbol(item.symbol)) || item);
        writeWatchlist(merged);
        watchlistRealtimeLoaded = true;
        renderWatchlist();
        if (ruleFeedback) ruleFeedback.textContent = data.errors?.length ? `实时刷新完成，${data.errors.length} 个标的暂未获取到远程数据。` : `实时刷新完成：${data.refreshed_at || ''}`;
      } catch (err) {
        if (ruleFeedback) ruleFeedback.textContent = err.message || '实时数据获取失败，请稍后重试。';
      } finally {
        watchlistRealtimeInFlight = false;
        if (refreshValuationButton) refreshValuationButton.disabled = false;
      }
    };
    const renderWatchlist = () => {
      if (!watchlistBody || !watchlistEmpty) return;
      const items = readWatchlist();
      if (items.some(item => item.valuationSource === 'legacy-cleared')) writeWatchlist(items);
      renderWatchlistHeader(items);
      watchlistBody.replaceChildren();
      watchlistEmpty.hidden = items.length > 0;
      items.forEach(item => {
        const row = document.createElement('tr');
        row.className = ['status-low','status-normal','status-high'].includes(item.status) ? item.status : 'status-normal';
        const nameCell = document.createElement('td');
        nameCell.className = 'watchlist-name-cell';
        const name = document.createElement('span');
        name.className = 'watchlist-name-main';
        const nameLabel = document.createElement('strong');
        nameLabel.textContent = item.name || item.symbol;
        const codeLabel = document.createElement('small');
        codeLabel.textContent = item.symbol || '';
        name.append(nameLabel, codeLabel);
        const remove = document.createElement('button');
        remove.type = 'button'; remove.className = 'favorite-remove'; remove.title = '取消收藏'; remove.setAttribute('aria-label', `取消收藏 ${item.name}`);
        remove.innerHTML = '<svg class="ui-icon" aria-hidden="true"><use href="#icon-star"/></svg>';
        remove.addEventListener('click', () => { writeWatchlist(readWatchlist().filter(entry => entry.symbol !== item.symbol)); renderWatchlist(); });
        nameCell.append(name, remove); row.append(nameCell);
        const values = [item.conclusion,item.latestValue,item.pe,item.pb,item.position,item.drawdown,item.rsi,item.ma20,item.ma60,item.exchangeFund,item.offExchangeFund];
        values.forEach((value, index) => {
          const cell = document.createElement('td');
          if (index === 0) { const label = document.createElement('span'); label.className = 'valuation-label'; label.textContent = value; cell.append(label); }
          else {
            cell.textContent = value || '';
            if (!value) cell.className = 'blank-value';
            if ((index === 2 || index === 3) && item.valuationNote) cell.title = item.valuationNote;
            if (index === 1 && item.isStaleMarketData) {
              cell.classList.add('stale-value');
              cell.textContent = '待更新';
              if (item.latestValueNote) cell.title = `旧行情数值已隐藏，${item.latestValueNote}`;
            }
          }
          row.append(cell);
        });
        watchlistBody.append(row);
      });
      favoriteButtons.forEach(button => {
        const saved = items.some(item => normalizeWatchlistSymbol(item.symbol) === normalizeWatchlistSymbol(button.dataset.symbol));
        const text = button.querySelector('.favorite-text') || button.querySelector('span');
        button.classList.toggle('active', saved);
        button.setAttribute('aria-pressed', saved ? 'true' : 'false');
        button.title = saved ? '已加入挑选' : '收藏到挑选';
        button.setAttribute('aria-label', saved ? '已加入挑选' : '收藏到挑选');
        if (text) text.textContent = saved ? '已收藏' : (button.classList.contains('favorite-overview') ? '收藏到挑选' : '收藏当前标的');
      });
      if (!watchlistRealtimeLoaded && !watchlistRealtimeInFlight && items.length) {
        setTimeout(refreshWatchlistRealtime, 0);
      }
    };
    const buildWatchlistItem = button => {
      const symbol = normalizeWatchlistSymbol(button.dataset.symbol || '000300');
      const payload = parseWatchlistPayload(button);
      return normalizeWatchlistItem({
        symbol,
        name:button.dataset.name || payload.name || fallbackSecurityName(symbol),
        status:'status-normal',
        conclusion:'待刷新',
        stars:'',
        earningsYield:'',
        pe:'',
        pb:'',
        dividend:'',
        roe:'',
        exchangeFund:'',
        offExchangeFund:'',
        metricMode:'market',
        valuationSource:'no-valuation',
        ...payload,
        symbol,
      });
    };
    favoriteButtons.forEach(button => {
      button.addEventListener('click', () => {
        const items = readWatchlist();
        const symbol = normalizeWatchlistSymbol(button.dataset.symbol || '000300');
        const exists = items.some(item => normalizeWatchlistSymbol(item.symbol) === symbol);
        writeWatchlist(exists ? items.filter(item => normalizeWatchlistSymbol(item.symbol) !== symbol) : [...items, buildWatchlistItem(button)]);
        renderWatchlist();
      });
    });
    renderWatchlist();
    const homeGroup = document.querySelector('.side-home-group');
    const homeSummary = homeGroup?.querySelector('[data-home-summary]');
    const accountGroup = document.querySelector('.side-account-group');
    const accountSummary = accountGroup?.querySelector('[data-account-summary]');
    const syncHomeGroupState = (expanded) => {
      if (homeSummary) homeSummary.setAttribute('aria-expanded', expanded ? 'true' : 'false');
    };
    const syncAccountGroupState = (expanded) => {
      if (accountSummary) accountSummary.setAttribute('aria-expanded', expanded ? 'true' : 'false');
    };
    syncHomeGroupState(Boolean(homeGroup?.open));
    syncAccountGroupState(Boolean(accountGroup?.open));
    homeGroup?.addEventListener('toggle', () => syncHomeGroupState(Boolean(homeGroup.open)));
    accountGroup?.addEventListener('toggle', () => syncAccountGroupState(Boolean(accountGroup.open)));
    const activateWorkspace = targetId => {
      document.body.dataset.activeWorkspace = targetId;
      document.querySelectorAll('[data-workspace-view]').forEach(view => { view.hidden = view.id !== targetId; });
      document.querySelectorAll('[data-workspace-target]').forEach(item => item.classList.toggle('active', item.dataset.workspaceTarget === targetId));
      if (homeGroup && ['home-workspace','select-workspace','buy-workspace','sell-workspace','agent-workspace'].includes(targetId)) {
        homeGroup.open = true;
        syncHomeGroupState(true);
      }
      if (accountGroup && ['account-workspace','plan-workspace'].includes(targetId)) {
        accountGroup.open = true;
        syncAccountGroupState(true);
      }
      document.getElementById(targetId)?.scrollIntoView({ block:'start' });
    };
    document.querySelectorAll('[data-workspace-target]').forEach(link => link.addEventListener('click', (event) => {
      if (link.hasAttribute('data-home-summary')) {
        const targetId = link.dataset.workspaceTarget;
        history.replaceState(null, '', `#${targetId}`);
        activateWorkspace(targetId);
        return;
      }
      event.preventDefault();
      const targetId = link.dataset.workspaceTarget;
      history.replaceState(null, '', `#${targetId}`);
      activateWorkspace(targetId);
    }));
    const workspaceIds = ['home-workspace','select-workspace','buy-workspace','sell-workspace','agent-workspace','account-workspace','plan-workspace','result-panel'];
    const initialWorkspace = workspaceIds.includes(location.hash.slice(1)) ? location.hash.slice(1) : 'home-workspace';
    activateWorkspace(initialWorkspace);
    window.addEventListener('hashchange', () => {
      const targetId = workspaceIds.includes(location.hash.slice(1)) ? location.hash.slice(1) : 'home-workspace';
      activateWorkspace(targetId);
    });
    const planEditor = document.getElementById('planEditor');
    const planTemplateBox = document.getElementById('planTemplateBox');
    const planMeta = document.getElementById('planMeta');
    const planStorageKey = 'quant-plan-content-v1';
    const planModeKey = 'quant-plan-mode-v1';
    const defaultPlanTemplate = planTemplateBox?.textContent || '';
    const applyPlanMode = (mode) => {
      document.querySelectorAll('[data-plan-mode]').forEach(button => button.classList.toggle('active', button.dataset.planMode === mode));
      if (planTemplateBox) planTemplateBox.hidden = mode !== 'template';
      if (planEditor && mode === 'template' && !planEditor.value.trim()) planEditor.value = defaultPlanTemplate;
      try { localStorage.setItem(planModeKey, mode); } catch (_) {}
    };
    if (planEditor) {
      try {
        const savedPlan = localStorage.getItem(planStorageKey);
        if (savedPlan) planEditor.value = savedPlan;
      } catch (_) {}
      planEditor.addEventListener('input', () => {
        try {
          localStorage.setItem(planStorageKey, planEditor.value);
          if (planMeta) planMeta.textContent = '已自动保存在本地。';
        } catch (_) {
          if (planMeta) planMeta.textContent = '本地保存不可用，内容仅保留在当前页面。';
        }
      });
    }
    const initialPlanMode = (() => {
      try { return localStorage.getItem(planModeKey) || 'template'; } catch (_) { return 'template'; }
    })();
    applyPlanMode(initialPlanMode);
    document.querySelectorAll('[data-plan-mode]').forEach(button => button.addEventListener('click', () => {
      applyPlanMode(button.dataset.planMode || 'template');
      if (button.dataset.planMode === 'template' && planEditor && !planEditor.value.trim()) {
        planEditor.value = defaultPlanTemplate;
      }
    }));
    const renderBacktestChart = (key = 'all') => {
      document.querySelectorAll('.backtest-scale').forEach(item => item.classList.toggle('active', item.dataset.timeScale === key));
      const root = document.querySelector('[data-backtest-chart]');
      if (!root) return;
      const svg = root.querySelector('svg');
      const empty = document.getElementById('workspace-backtest-empty');
      const readJson = selector => {
        try { return JSON.parse(root.querySelector(selector)?.textContent || '[]'); } catch (_) { return []; }
      };
      if (svg) svg.style.display = '';
      if (empty) empty.hidden = true;
      const ranges = { '1y':365, '3y':1095, '5y':1825, all:null };
      const parseDate = value => {
        const date = new Date(`${value}T00:00:00`);
        return Number.isNaN(date.getTime()) ? null : date;
      };
      const scopePoints = points => {
        const valid = points.filter(point => point && point.date && Number.isFinite(Number(point.value)));
        if (!valid.length || !ranges[key]) return valid;
        const lastDate = parseDate(valid[valid.length - 1].date);
        if (!lastDate) return valid;
        const cutoff = new Date(lastDate);
        cutoff.setDate(cutoff.getDate() - ranges[key]);
        return valid.filter(point => {
          const date = parseDate(point.date);
          return date && date >= cutoff;
        });
      };
      const strategy = scopePoints(readJson('.backtest-equity-data'));
      const benchmark = scopePoints(readJson('.backtest-benchmark-data'));
      const dates = strategy.map(point => point.date);
      if (!strategy.length || !benchmark.length || !svg) {
        if (svg) svg.style.display = 'none';
        if (empty) { empty.hidden = false; empty.textContent = '券商回测数据不足，暂无法绘制。'; }
        return;
      }
      const normalizeReturn = points => {
        const first = Number(points[0]?.value);
        return points.map(point => ({ date:point.date, value:(Number(point.value) / first - 1) * 100 }));
      };
      const strategyReturn = normalizeReturn(strategy);
      const benchmarkReturn = normalizeReturn(benchmark);
      let peak = strategyReturn[0]?.value || 0;
      const drawdown = strategyReturn.map(point => {
        peak = Math.max(peak, point.value);
        return { date:point.date, value:point.value - peak };
      });
      const allValues = [...strategyReturn, ...benchmarkReturn, ...drawdown].map(point => point.value).filter(Number.isFinite);
      const minValue = Math.min(...allValues, 0);
      const maxValue = Math.max(...allValues, 0);
      const pad = Math.max((maxValue - minValue) * 0.12, 1);
      const yMin = minValue - pad;
      const yMax = maxValue + pad;
      const width = 980, height = 360, left = 64, right = 24, top = 28, bottom = 46;
      const chartW = width - left - right;
      const chartH = height - top - bottom;
      const xFor = index => left + (chartW * index / Math.max(1, strategyReturn.length - 1));
      const yFor = value => height - bottom - ((value - yMin) / Math.max(0.000001, yMax - yMin)) * chartH;
      const pathFor = points => {
        const coords = points.map((point, index) => ({ x:xFor(index), y:yFor(point.value) })).filter(point => Number.isFinite(point.x) && Number.isFinite(point.y));
        if (!coords.length) return '';
        if (coords.length < 3) return coords.map((point, index) => `${index ? 'L' : 'M'}${point.x.toFixed(1)} ${point.y.toFixed(1)}`).join(' ');
        let path = `M${coords[0].x.toFixed(1)} ${coords[0].y.toFixed(1)}`;
        for (let index = 0; index < coords.length - 1; index += 1) {
          const p0 = coords[Math.max(0, index - 1)];
          const p1 = coords[index];
          const p2 = coords[index + 1];
          const p3 = coords[Math.min(coords.length - 1, index + 2)];
          path += ` C${(p1.x + (p2.x - p0.x) / 6).toFixed(1)} ${(p1.y + (p2.y - p0.y) / 6).toFixed(1)} ${(p2.x - (p3.x - p1.x) / 6).toFixed(1)} ${(p2.y - (p3.y - p1.y) / 6).toFixed(1)} ${p2.x.toFixed(1)} ${p2.y.toFixed(1)}`;
        }
        return path;
      };
      const yLabels = [yMax, (yMax + yMin) / 2, yMin].map(value => `${value.toFixed(1)}%`);
      const xLabels = dates.length <= 1 ? dates : [dates[0], dates[Math.floor(dates.length / 2)], dates[dates.length - 1]];
      let grid = `<rect width="${width}" height="${height}" fill="#fff"/>`;
      yLabels.forEach((label, index) => {
        const y = top + chartH * index / Math.max(1, yLabels.length - 1);
        grid += `<path d="M${left} ${y.toFixed(1)}H${width - right}" stroke="#edf1f5"/>`;
        grid += `<text x="${left - 8}" y="${(y + 4).toFixed(1)}" text-anchor="end" fill="#667085" font-size="11">${label}</text>`;
      });
      xLabels.forEach((label, index) => {
        const x = left + chartW * index / Math.max(1, xLabels.length - 1);
        grid += `<path d="M${x.toFixed(1)} ${top}V${height - bottom}" stroke="#f2f5f8"/>`;
        grid += `<text x="${x.toFixed(1)}" y="${height - 14}" text-anchor="middle" fill="#667085" font-size="11">${label}</text>`;
      });
      grid += `<path d="M${left} ${top}V${height - bottom}H${width - right}" stroke="#98a2b3" fill="none"/>`;
      const lastStrategy = strategyReturn[strategyReturn.length - 1]?.value;
      svg.innerHTML = [
        grid,
        `<path d="${pathFor(strategyReturn)}" fill="none" stroke="#2563eb" stroke-width="2.7" stroke-linecap="round" stroke-linejoin="round"/>`,
        `<path d="${pathFor(benchmarkReturn)}" fill="none" stroke="#f59e0b" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"/>`,
        `<path d="${pathFor(drawdown)}" fill="none" stroke="#93c5fd" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/>`,
        `<text x="${width - right}" y="20" text-anchor="end" fill="#172033" font-size="12" font-weight="700">${brokerDataSourceLabel} · ${key === 'all' ? '全部' : key} · 策略 ${Number.isFinite(lastStrategy) ? lastStrategy.toFixed(2) : '-'}%</text>`
      ].join('');
    };
    window.applyBacktestScale = renderBacktestChart;
    document.querySelectorAll('.backtest-scale').forEach(button => button.addEventListener('click', () => renderBacktestChart(button.dataset.timeScale || 'all')));
    renderBacktestChart('all');
    const sellPresets = {
      profit:['30%','估值分位高于 80%','分批减仓提醒','盈利达到目标后分批复核，不因为单日波动直接卖出。'],
      valuation:['20%','估值分位高于 90%','提醒复核','估值进入高位区间时提醒复核，同时观察盈利和回撤。'],
      hold:['','估值分位高于 90%','仅记录不提醒','长期持有，不设置主动卖出条件，只记录风险变化。'],
      custom:['','估值分位高于 80%','提醒复核','']
    };
    const applySellStrategy = key => {
      document.querySelectorAll('[data-sell-strategy]').forEach(item => item.classList.toggle('active', item.dataset.sellStrategy === key));
      const [profit, valuation, action, rule] = sellPresets[key] || sellPresets.custom;
      document.getElementById('profitTarget').value = profit;
      document.getElementById('valuationLimit').value = valuation;
      document.getElementById('sellAction').value = action;
      document.getElementById('customSellRule').value = rule;
    };
    window.applySellStrategy = applySellStrategy;
    document.querySelectorAll('[data-sell-strategy]').forEach(button => button.addEventListener('click', () => applySellStrategy(button.dataset.sellStrategy)));
    const agentRule = document.getElementById('agentRule');
    const agentOutput = document.getElementById('agentOutput');
    const agentFrequency = document.getElementById('agentFrequency');
    const agentName = document.getElementById('agentName');
    const agentGoal = document.getElementById('agentGoal');
    const agentGuardrail = document.getElementById('agentGuardrail');
    const createdAgentList = document.getElementById('createdAgentList');
    const createdAgentCount = document.getElementById('createdAgentCount');
    const startAgentBuild = document.getElementById('startAgentBuild');
    const createdAgentStorageKey = 'quant-created-agents-v1';
    const readCreatedAgents = () => {
      try {
        const parsed = JSON.parse(localStorage.getItem(createdAgentStorageKey) || '[]');
        return Array.isArray(parsed) ? parsed : [];
      } catch (_) {
        return [];
      }
    };
    const writeCreatedAgents = agents => {
      try { localStorage.setItem(createdAgentStorageKey, JSON.stringify(agents)); } catch (_) { /* 本地存储不可用时只更新当前页面 */ }
    };
    const renderCreatedAgents = () => {
      const agents = readCreatedAgents();
      if (createdAgentCount) createdAgentCount.textContent = `${agents.length} 个`;
      if (!createdAgentList) return;
      createdAgentList.replaceChildren();
      if (!agents.length) {
        const empty = document.createElement('div');
        empty.className = 'created-agent-empty';
        empty.textContent = '还没有创建智能体';
        createdAgentList.append(empty);
        return;
      }
      agents.forEach(agentItem => {
        const card = document.createElement('article');
        card.className = 'created-agent-item';
        const title = document.createElement('strong');
        title.textContent = agentItem.name || '未命名智能体';
        const meta = document.createElement('div');
        meta.className = 'created-agent-meta';
        [agentItem.frequency, agentItem.rule, agentItem.output, agentItem.createdAt].filter(Boolean).forEach(text => {
          const span = document.createElement('span');
          span.textContent = text;
          meta.append(span);
        });
        const actions = document.createElement('div');
        actions.className = 'created-agent-actions';
        const useButton = document.createElement('button');
        useButton.type = 'button';
        useButton.textContent = '选用';
        useButton.addEventListener('click', () => {
          if (agentName) agentName.value = agentItem.name || '';
          if (agentFrequency) agentFrequency.value = agentItem.frequency || agentFrequency.value;
          if (agentRule) agentRule.value = agentItem.rule || agentRule.value;
          if (agentOutput) agentOutput.value = agentItem.output || agentOutput.value;
          if (agentGoal) agentGoal.value = agentItem.goal || agentGoal.value;
          if (agentGuardrail) agentGuardrail.value = agentItem.guardrail || agentGuardrail.value;
          syncAgentPreview();
          document.getElementById('agentPreviewStatus').textContent = '已创建';
        });
        const deleteButton = document.createElement('button');
        deleteButton.type = 'button';
        deleteButton.textContent = '删除';
        deleteButton.addEventListener('click', () => {
          writeCreatedAgents(readCreatedAgents().filter(entry => entry.id !== agentItem.id));
          renderCreatedAgents();
        });
        actions.append(useButton, deleteButton);
        card.append(title, meta, actions);
        createdAgentList.append(card);
      });
    };
    startAgentBuild?.addEventListener('click', () => {
      document.getElementById('agentBuilderForm')?.scrollIntoView({ behavior:'smooth', block:'start' });
      agentName?.focus();
      agentName?.select?.();
    });
    const syncAgentPreview = () => {
      document.getElementById('agentPreviewRule').textContent = agentRule?.value || '';
      document.getElementById('agentPreviewOutput').textContent = agentOutput?.value || '';
      document.getElementById('agentPreviewFrequency').textContent = agentFrequency?.value || '';
    };
    [agentRule,agentOutput,agentFrequency].forEach(control => control?.addEventListener('change', syncAgentPreview));
    document.getElementById('agentBuilderForm')?.addEventListener('submit', event => {
      event.preventDefault(); syncAgentPreview();
      document.getElementById('agentPreviewStatus').textContent = '已创建';
      document.getElementById('agentBuildFeedback').textContent = '智能体配置已保存，可按设定频率运行。';
      const item = {
        id:`agent-${Date.now()}`,
        name:agentName?.value?.trim() || '未命名智能体',
        frequency:agentFrequency?.value || '',
        rule:agentRule?.value || '',
        output:agentOutput?.value || '',
        goal:agentGoal?.value || '',
        guardrail:agentGuardrail?.value || '',
        createdAt:new Date().toLocaleString('zh-CN', { hour12:false })
      };
      writeCreatedAgents([item, ...readCreatedAgents().filter(entry => entry.name !== item.name)].slice(0, 12));
      renderCreatedAgents();
    });
    renderCreatedAgents();
    document.querySelectorAll('[data-symbol-preset]').forEach(button => button.addEventListener('click', () => {
      const input = document.getElementById('homeSymbol') || document.getElementById('symbol');
      if (!input) return;
      input.value = button.dataset.symbolPreset || '';
      input.focus();
    }));
    document.querySelectorAll('.metric-option').forEach(button => button.addEventListener('click', () => {
      document.querySelectorAll('.metric-option').forEach(item => item.classList.toggle('active', item === button));
      const selected = button.textContent.trim();
      const secondary = document.querySelector('.secondary-metric');
      if (secondary) secondary.textContent = selected === '估值' ? '二把手：市净率' : `当前选择：${selected}`;
    }));
    const symbolInput = document.getElementById('symbol');
    const syncSymbolPlaceholder = () => {
      if (symbolInput) symbolInput.placeholder = window.matchMedia('(max-width: 900px)').matches ? '输入代码/名称' : '输入 基金/股票/债券 代码/名称';
    };
    syncSymbolPlaceholder();
    window.addEventListener('resize', syncSymbolPlaceholder);
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
    document.querySelectorAll('form').forEach(form => form.addEventListener('submit', () => {
      const mode = form.querySelector('[name="mode"]')?.value || '';
      if (!['analyze','chat'].includes(mode)) return;
      const overlay = document.getElementById('submitOverlay');
      const hint = document.getElementById('submitOverlayHint');
      if (hint) hint.textContent = '正在拉取行情、计算指标和生成图表，通常需要 5-15 秒。';
      overlay?.classList.add('active');
      window.setTimeout(() => {
        if (overlay?.classList.contains('active') && hint) {
          hint.textContent = '仍在处理数据，可能是行情接口较慢。请继续等待，或稍后刷新后重试。';
        }
      }, 20000);
    }));
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
        reader_version: document.getElementById('reader_version')?.value || '个人投资者版',
        toggles,
        form: {
          symbol: document.getElementById('symbol')?.value || '',
          market: document.getElementById('market')?.value || '',
          period: document.getElementById('period')?.value || '',
          start_date: document.getElementById('start_date')?.value || '',
          end_date: document.getElementById('end_date')?.value || '',
          use_ai: document.getElementById('use_ai')?.value || '',
          reader_version: document.getElementById('reader_version')?.value || ''
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
    const actionFeedback = document.getElementById('reportActionFeedback');
    const showActionFeedback = (text) => {
      if (!actionFeedback) return;
      actionFeedback.hidden = false;
      actionFeedback.textContent = text;
    };
    const showShareLinkFeedback = (link, copied) => {
      if (!actionFeedback) return;
      actionFeedback.hidden = false;
      actionFeedback.replaceChildren();
      const message = document.createElement('div');
      message.textContent = copied ? '分享链接已复制。' : '分享链接已生成，浏览器未允许自动复制，请手动复制。';
      const input = document.createElement('input');
      input.type = 'text';
      input.readOnly = true;
      input.value = link || '';
      input.addEventListener('focus', () => input.select());
      actionFeedback.append(message, input);
      input.select();
    };
    const copyTextSafely = async text => {
      if (!text) return false;
      try {
        if (navigator.clipboard?.writeText) {
          await navigator.clipboard.writeText(text);
          return true;
        }
      } catch (_) {
        return false;
      }
      return false;
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
        const copied = await copyTextSafely(link);
        showShareLinkFeedback(link, copied);
      } catch (err) {
        showActionFeedback('分享链接生成失败，请稍后重试。');
      }
    }));
    const readerFallbacks = {
      '个人投资者版': {
        note: '当前：个人投资者版',
        conclusion: '关注回撤、数据完整性和持仓集中度。'
      },
      '小资金账户版': {
        note: '当前：小资金账户版',
        conclusion: '关注仓位、承受亏损和交易成本。'
      },
      '业余量化版': {
        note: '当前：业余量化版',
        conclusion: '关注收益、回撤、波动和样本区间。'
      },
      '小型投研团队版': {
        note: '当前：小型投研团队版',
        conclusion: '关注数据来源、风险边界和复盘记录。'
      }
    };
    const applyReaderVersion = (version, payload) => {
      const preset = payload || readerFallbacks[version] || readerFallbacks['个人投资者版'];
      const input = document.getElementById('reader_version');
      const conclusion = document.querySelector('[data-followup-context]');
      if (input) input.value = version;
      if (conclusion) conclusion.textContent = preset.conclusion || conclusion.textContent;
    };
    document.getElementById('reader_version')?.addEventListener('change', async (event) => {
      const version = event.target.value || '个人投资者版';
      applyReaderVersion(version);
      try {
        const data = await postJson('{{ url_for("reader_version_api") }}', { version });
        applyReaderVersion(version, data);
      } catch (err) {
        event.target.title = err.message || '读者版本保存失败。';
      }
    });
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
  </script>
</body>
</html>
"""

__all__ = ["PAGE_TEMPLATE"]
