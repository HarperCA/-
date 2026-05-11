# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import traceback
from datetime import datetime
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

from flask import jsonify, render_template_string, request, url_for

from web_modules.templates import DASHBOARD_PAGE_TEMPLATE, PAGE_TEMPLATE


def register_main_routes(app, deps: dict) -> None:
    _current_user = deps["current_user"]
    _ensure_user_space = deps["ensure_user_space"]
    _normalize_market = deps["normalize_market"]
    _normalize_symbol = deps["normalize_symbol"]
    _normalize_period = deps["normalize_period"]
    _run_analysis = deps["run_analysis"]
    _handle_prompt = deps["handle_prompt"]
    _parse_bounded_float = deps["parse_bounded_float"]
    _validate_buy_date = deps["validate_buy_date"]
    _current_holdings_mgr = deps["current_holdings_mgr"]
    _sync_sqlite_user_data = deps["sync_sqlite_user_data"]
    _read_alerts = deps["read_alerts"]
    _write_alerts = deps["write_alerts"]
    _evaluate_alerts = deps["evaluate_alerts"]
    _read_automations = deps["read_automations"]
    _write_automations = deps["write_automations"]
    _reload_user_jobs = deps["reload_user_jobs"]
    _automation_job_runner = deps["automation_job_runner"]
    _friendly_error = deps["friendly_error"]
    _consume_notifications = deps["consume_notifications"]
    _read_history = deps["read_history"]
    _read_automation_log = deps["read_automation_log"]
    _cache_count = deps["cache_count"]
    _list_recent_reports = deps["list_recent_reports"]
    _bounded_int = deps["bounded_int"]
    _normalize_run_time = deps["normalize_run_time"]
    _user_dir = deps["user_dir"]
    _shared_reports_dir = deps["shared_reports_dir"]
    agent = deps["agent"]

    _READER_NOTES = {
        "个人投资者版": "个人投资者版：用通俗语言解释过去表现、近期变化、回撤风险和下一步观察清单。",
        "小资金账户版": "小资金账户版：重点看仓位是否过重、继续下跌能否承受、手续费和频繁交易是否影响收益。",
        "业余量化版": "业余量化版：保留收益、回撤、波动、样本区间和参数观察，但明确只是复核工具。",
        "小型投研团队版": "小型投研团队版：强调数据来源、资料引用、风险边界和可追溯复盘流程。",
        "研究员版": "研究员版：保留收益、回撤、波动和资料依据，但输出仍保持复盘与风险报告口径。",
        "小白版本": "小白版本：用直白语言解释收益、风险和下一步观察点，减少专业术语。",
        "老板速读版": "老板速读版：先给复盘结论，再讲风险、集中度、是否需要继续复核。",
        "客户展示版": "客户展示版：强调数据来源、风险提示和可读性，不写成直接投资建议。",
        "风控审核版": "风控审核版：聚焦最大回撤、波动、集中度、异常月份和建议措辞边界。",
    }
    _READER_CONCLUSIONS = {
        "个人投资者版": "过去表现需要和风险一起看。当前报告用于复盘和识别风险，下一步应重点观察回撤是否扩大、数据是否完整、持仓是否过于集中。",
        "小资金账户版": "小资金账户应优先控制试错成本。先复核单一持仓占比、继续下跌时的可承受亏损，以及交易成本是否会吞掉收益。",
        "业余量化版": "参数和观察信号只用于研究复核，不能理解为收益保证或交易规则。下一步应做样本外验证、回撤区间复盘和参数敏感性检查。",
        "小型投研团队版": "报告适合作为复盘底稿：保留数据来源、风险解释和观察清单，避免写成直接买卖建议。",
        "研究员版": "当前报告用于复盘和风险识别，不是机构终端结论。下一步应复核数据完整性、风险暴露和样本外表现。",
        "小白版本": "简单说：先看过去表现，再看亏损会不会太大。当前只建议观察和补数据，不给直接买卖指令。",
        "老板速读版": "结论：报告可作为复盘底稿，重点看风险是否可承受、持仓是否集中、是否需要继续验证。",
        "客户展示版": "本报告展示数据状态、风险提示和后续复核动作，结论以观察为主，不构成投资建议。",
        "风控审核版": "风控关注：复核最大回撤、波动率、集中度和异常月份，避免输出确定性买卖指令。",
    }
    _DASHBOARD_RETURN_PRESETS = {
        "近一周": {"portfolio_return": "+1.36%", "benchmark_return": "+0.42%", "portfolio_path": "M20,172 C96,168 126,148 176,152 S276,132 332,116 S462,102 585,82", "benchmark_path": "M20,178 C108,182 160,166 218,170 S338,158 418,146 S512,139 585,132"},
        "近一月": {"portfolio_return": "+3.82%", "benchmark_return": "+1.08%", "portfolio_path": "M20,176 C78,170 110,152 150,160 S226,130 284,138 S392,98 456,86 S535,94 585,70", "benchmark_path": "M20,180 C92,186 132,168 188,174 S286,156 348,162 S464,136 585,126"},
        "近三月": {"portfolio_return": "+6.47%", "benchmark_return": "+1.92%", "portfolio_path": "M20,185 C80,176 100,142 150,150 S230,106 285,120 S360,92 430,70 S520,64 585,52", "benchmark_path": "M20,188 C88,198 126,168 184,176 S280,150 350,158 S460,130 585,112"},
        "今年以来": {"portfolio_return": "+11.12%", "benchmark_return": "+2.31%", "portfolio_path": "M20,160 C75,150 90,110 140,130 S215,85 260,100 S345,72 395,48 S480,42 520,70 S560,88 585,76", "benchmark_path": "M20,170 C90,205 100,160 145,185 S240,160 285,178 S380,170 430,145 S515,155 585,138"},
        "近一年": {"portfolio_return": "+18.64%", "benchmark_return": "+5.72%", "portfolio_path": "M20,198 C76,184 98,150 144,162 S216,116 276,126 S360,80 424,72 S510,42 585,34", "benchmark_path": "M20,206 C98,214 142,176 198,184 S292,160 360,166 S470,130 585,118"},
        "全部": {"portfolio_return": "+127.64%", "benchmark_return": "+37.40%", "portfolio_path": "M20,210 C82,198 116,164 162,174 S244,116 304,130 S384,72 450,82 S526,38 585,26", "benchmark_path": "M20,216 C96,224 140,188 198,194 S292,166 364,174 S470,138 585,126"},
    }
    _EXPLANATIONS = {
        "标的": "本次分析对象的代码或资产名称，例如基金、股票、指数或数字资产。",
        "市场": "标的所属市场类型。系统会按市场选择对应的数据源、代码规范和分析口径。",
        "周期": "本次回测或分析使用的时间范围，影响样本数量、收益和风险统计。",
        "最新价格": "数据源可获取到的最近一个交易日或采样点价格。",
        "数据区间": "实际参与计算的数据起止日期，不一定等于用户选择的回测区间。",
        "样本数": "参与指标计算的有效数据点数量。样本越少，统计结果越容易不稳定。",
        "年化收益": "把区间收益换算为一年维度后的收益率，用于比较不同周期策略的收益水平。",
        "超额收益": "策略收益减去基准收益后的差额，用来衡量是否跑赢基准。",
        "累计收益": "从起始日期到结束日期的总收益，不做年化处理。",
        "年化波动率": "收益率波动按一年维度换算后的风险指标，数值越高代表净值起伏越大。",
        "夏普比率": "单位风险带来的超额收益。通常越高越好，低于 1 说明收益质量仍需谨慎验证。",
        "最大回撤": "从历史高点跌到后续低点的最大跌幅，用来衡量最糟糕持有体验。",
        "胜率": "盈利周期占全部统计周期的比例。胜率高不等于收益高，还要结合盈亏比。",
        "跟踪误差": "策略相对基准收益差的波动程度，越高说明策略偏离基准越明显。",
        "因子类别": "因子所属的大类，例如价值、成长、质量、动量或情绪。",
        "因子名称": "具体用于解释或打分的变量名称，是信号矩阵里的核心对象。",
        "方向": "因子与未来收益的预期关系。正向通常表示数值越高越偏多，负向相反。",
        "IC 均值": "Information Coefficient 的均值，表示因子分数与后续收益排序的相关性。",
        "IC_IR": "IC 的稳定性指标，通常是 IC 均值除以 IC 波动。越高说明因子越稳定。",
        "多头暴露": "策略在该因子高分资产上的暴露程度。",
        "空头暴露": "策略在该因子低分资产上的暴露程度。",
        "结论": "系统根据因子方向、IC 和暴露情况给出的简化判断。",
        "市盈率 PE": "价格相对每股盈利的估值指标。PE 越高通常代表估值越贵，但成长行业需要结合增速判断。",
        "营收增速 TTM": "最近十二个月收入同比增长速度，用来观察公司或组合成分的成长性。",
        "ROE TTM": "最近十二个月净资产收益率，衡量公司利用股东权益创造利润的能力。",
        "20日价格动量": "过去约 20 个交易日价格变化形成的趋势信号，常用于判断短期惯性。",
        "成交量异动": "成交量相对常态的放大或收缩，用来辅助识别资金关注度和情绪变化。",
        "归因项": "把超额收益拆成不同来源的分析维度，例如行业、风格、个股。",
        "配置效应": "因资产、行业或风格配置比例不同带来的收益贡献。",
        "选股效应": "在同一配置框架内，具体标的选择带来的收益贡献。",
        "交互效应": "配置和选股共同作用产生的剩余贡献。",
        "合计超额": "各项归因贡献汇总后的超额收益。",
        "行业": "按行业维度拆解收益来源，观察行业配置是否贡献超额。",
        "风格": "按风格因子拆解收益来源，例如价值、成长、质量、动量等。",
        "个股": "具体证券选择带来的收益贡献。",
        "年度": "收益统计所属年份或年度汇总列。",
        "模型名称": "当前报告采用的策略或分析模型名称。",
        "基准口径": "用于对比策略表现的参考标的或指数。",
        "因子来源": "因子数据来自基本面、技术面、情绪面或其他数据源。",
        "调仓频率": "策略重新计算权重或调整组合的频率。",
        "交易成本假设": "回测中对手续费、滑点等交易成本的估计。",
        "AI 解读": "是否启用大模型对数据结果进行文字解释和审校。",
        "最大回撤阈值": "风控允许的最大历史回撤警戒线，超过后需要重点复核。",
        "单日最大亏损": "单日亏损的风控警戒线，用于识别异常波动。",
        "行业最大暴露": "单一行业允许的最大仓位或风险暴露比例。",
        "个股最大权重": "单一证券允许的最大持仓比例，用来控制集中度风险。",
        "换手率上限": "组合在一个周期内允许的最大交易活跃度，过高会放大成本和滑点。",
        "数据一致性": "检查报告中的数据、图表和指标引用是否互相一致。",
        "指标引用": "检查文字结论引用的指标是否存在且数值口径一致。",
        "风险提示": "检查报告是否补充了回撤、波动、集中度等必要风险说明。",
        "投资建议措辞": "检查报告是否避免直接买卖指令，保持研究观察口径。",
    }

    def _normalize_backtest_date(value: str | None, field_name: str) -> str:
        value = (value or "").strip()
        if not value:
            return ""
        try:
            return datetime.strptime(value, "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError as exc:
            raise ValueError(f"{field_name}必须是 YYYY-MM-DD 格式。") from exc

    def _json_request() -> dict:
        data = request.get_json(silent=True)
        return data if isinstance(data, dict) else {}

    def _ui_state_path(username: str):
        _ensure_user_space(username)
        return _user_dir(username) / "ui_state.json"

    def _read_ui_state(username: str) -> dict:
        path = _ui_state_path(username)
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _write_ui_state(username: str, state: dict) -> None:
        path = _ui_state_path(username)
        path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    def _safe_share_page(value: str | None) -> str:
        raw = str(value or "").strip()
        if not raw:
            return ""
        parts = urlsplit(raw)
        if parts.scheme or parts.netloc:
            request_host = request.host.split(":", 1)[0]
            link_host = parts.netloc.split("@")[-1].split(":", 1)[0]
            if parts.scheme not in {"http", "https"} or link_host != request_host:
                return ""
        elif not raw.startswith("/") or raw.startswith("//"):
            return ""
        return urlunsplit(("", "", parts.path or "/", parts.query, ""))[:500]

    def _require_user_json() -> tuple[str | None, tuple | None]:
        username = _current_user()
        if not username:
            return None, (jsonify({"ok": False, "error": "请先登录后再执行这个操作。"}), 401)
        _ensure_user_space(username)
        return username, None

    @app.route("/api/ui/report_config", methods=["POST"])
    def save_report_config_api():
        username, error_response = _require_user_json()
        if error_response:
            return error_response
        payload = _json_request()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        state = _read_ui_state(username)
        config = {
            "saved_at": now,
            "page": _safe_share_page(payload.get("page") or request.referrer),
            "title": str(payload.get("title") or "投资复盘报告"),
            "reader_version": str(payload.get("reader_version") or state.get("reader_version") or "个人投资者版"),
            "toggles": payload.get("toggles") if isinstance(payload.get("toggles"), dict) else {},
            "form": payload.get("form") if isinstance(payload.get("form"), dict) else {},
        }
        state["report_config"] = config
        _write_ui_state(username, state)
        return jsonify({"ok": True, "message": f"已保存当前报告配置。保存时间：{now}", "config": config})

    @app.route("/api/ui/reader_version", methods=["POST"])
    def reader_version_api():
        username, error_response = _require_user_json()
        if error_response:
            return error_response
        version = str(_json_request().get("version") or "").strip()
        if version not in _READER_NOTES:
            return jsonify({"ok": False, "error": "不支持这个读者版本。"}), 400
        state = _read_ui_state(username)
        state["reader_version"] = version
        state["reader_version_saved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _write_ui_state(username, state)
        return jsonify({
            "ok": True,
            "version": version,
            "note": _READER_NOTES[version],
            "conclusion": _READER_CONCLUSIONS[version],
        })

    @app.route("/api/ui/share_link", methods=["POST"])
    def share_report_link_api():
        username, error_response = _require_user_json()
        if error_response:
            return error_response
        payload = _json_request()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        token = uuid4().hex[:16]
        share_dir = _shared_reports_dir()
        share_dir.mkdir(parents=True, exist_ok=True)
        state = _read_ui_state(username)
        snapshot = {
            "token": token,
            "owner": username,
            "created_at": now,
            "title": str(payload.get("title") or "投资复盘报告"),
            "page": _safe_share_page(payload.get("page") or request.referrer),
            "reader_version": str(payload.get("reader_version") or state.get("reader_version") or "个人投资者版"),
            "report_config": state.get("report_config", {}),
        }
        (share_dir / f"{token}.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
        return jsonify({"ok": True, "share_url": url_for("shared_report_page", token=token, _external=True), "snapshot": snapshot})

    @app.route("/share/<token>")
    def shared_report_page(token: str):
        if not token or not all(ch.isalnum() for ch in token):
            return "Not found", 404
        path = _shared_reports_dir() / f"{token}.json"
        if not path.exists():
            return "Not found", 404
        try:
            snapshot = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return "Not found", 404
        return render_template_string(
            """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{{ snapshot.title }}</title><style>body{margin:0;padding:28px;font:14px/1.7 "Microsoft YaHei",Arial,sans-serif;color:#111827;background:#f8fafc}.card{max-width:860px;margin:auto;background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:22px}h1{margin:0 0 10px;font-size:24px}.muted{color:#667085}.meta{display:grid;gap:8px;margin:18px 0;padding:14px;background:#f8fafc;border:1px solid #e5e7eb;border-radius:8px}a{color:#2563eb}</style></head><body><main class="card"><h1>{{ snapshot.title }}</h1><div class="muted">分享时间：{{ snapshot.created_at }} · 读者版本：{{ snapshot.reader_version }}</div><div class="meta"><div>这是一个报告配置快照链接。</div>{% if snapshot.page %}<div>原页面：<a href="{{ snapshot.page }}">{{ snapshot.page }}</a></div>{% endif %}</div><pre>{{ snapshot.report_config | tojson(indent=2) }}</pre></main></body></html>""",
            snapshot=snapshot,
        )

    @app.route("/api/ui/dashboard_action", methods=["POST"])
    def dashboard_action_api():
        username, error_response = _require_user_json()
        if error_response:
            return error_response
        action = str(_json_request().get("action") or "").strip()
        if action == "notifications":
            notifications = _consume_notifications(username)
            return jsonify({"ok": True, "message": f"已读取 {len(notifications)} 条通知。", "notifications": notifications})
        if action == "settings":
            state = _read_ui_state(username)
            return jsonify({"ok": True, "message": "已读取看板设置。", "settings": state})
        return jsonify({"ok": False, "error": "不支持这个看板动作。"}), 400

    @app.route("/api/ui/dashboard_returns")
    def dashboard_returns_api():
        range_name = (request.args.get("range") or "今年以来").strip()
        preset = _DASHBOARD_RETURN_PRESETS.get(range_name) or _DASHBOARD_RETURN_PRESETS["今年以来"]
        return jsonify({"ok": True, "range": range_name if range_name in _DASHBOARD_RETURN_PRESETS else "今年以来", **preset})

    @app.route("/api/ui/explain")
    def explain_metric_api():
        name = (request.args.get("name") or "").strip()
        if not name:
            return jsonify({"ok": False, "error": "缺少要解释的名称。"}), 400
        explanation = _EXPLANATIONS.get(name)
        if not explanation:
            explanation = f"{name} 是当前报告中的分析字段。它用于辅助理解收益、风险、因子有效性或报告口径，建议结合所在表格的数值和上下文一起判断。"
        return jsonify({"ok": True, "name": name, "explanation": explanation})

    @app.route("/portfolio", methods=["GET", "POST"])
    def portfolio_page():
        return index("holdings")


    @app.route("/alerts", methods=["GET", "POST"])
    def alerts_page():
        return index("alerts")


    @app.route("/automation", methods=["GET", "POST"])
    def automation_page():
        return index("automation")


    @app.route("/analysis_history", methods=["GET", "POST"])
    def analysis_history_page():
        return index("history")


    @app.route("/analysis", methods=["GET", "POST"])
    def analysis_page():
        return index("analysis")


    @app.route("/", methods=["GET", "POST"])
    def index(module_view: str | None = None):
        current_user = _current_user()
        if current_user:
            _ensure_user_space(current_user)
        result = None
        note = None
        error = None
        form = {
            "prompt": "",
            "symbol": "002982",
            "market": "fund",
            "period": "max",
            "start_date": "",
            "end_date": "",
            "use_ai": False,
        }

        if request.method == "POST":
            modes = request.form.getlist("mode")
            mode = modes[-1] if modes else ""
            try:
                if mode == "analyze":
                    market = _normalize_market(request.form.get("market", "fund"))
                    symbol = _normalize_symbol(request.form.get("symbol", ""), market)
                    period = _normalize_period(request.form.get("period", "max"))
                    start_date = _normalize_backtest_date(request.form.get("start_date"), "开始日期")
                    end_date = _normalize_backtest_date(request.form.get("end_date"), "结束日期")
                    if start_date and end_date and start_date > end_date:
                        raise ValueError("开始日期不能晚于结束日期。")
                    analysis_period = "max" if (start_date or end_date) else period
                    use_ai = request.form.get("use_ai", "false") == "true"
                    force_refresh = request.form.get("force_refresh", "false") == "true"
                    form.update({
                        "symbol": symbol,
                        "market": market,
                        "period": period,
                        "start_date": start_date,
                        "end_date": end_date,
                        "use_ai": use_ai,
                    })
                    if not symbol:
                        error = "请输入代码。"
                    else:
                        result = _run_analysis(
                            symbol,
                            market,
                            analysis_period,
                            use_ai,
                            force_refresh=force_refresh,
                            start_date=start_date or None,
                            end_date=end_date or None,
                        )
                elif mode == "chat":
                    prompt = (request.form.get("prompt", "") or "").strip()
                    if not prompt:
                        error = "请输入请求内容。"
                    else:
                        result, note, error, form = _handle_prompt(prompt)
                elif mode == "holding_add":
                    if not current_user:
                        error = "请先登录后再保存持仓。"
                    else:
                        market = _normalize_market(request.form.get("holding_market", "fund"))
                        symbol = _normalize_symbol(request.form.get("holding_symbol", ""), market)
                        quantity = _parse_bounded_float(request.form.get("holding_qty", ""), "数量", 0.000001, 1_000_000_000_000)
                        avg_cost = _parse_bounded_float(request.form.get("holding_cost", ""), "成本", 0, 1_000_000_000)
                        buy_date = _validate_buy_date(request.form.get("holding_date", ""))
                        if not symbol:
                            error = "请输入持仓代码。"
                        else:
                            _current_holdings_mgr().add(symbol, market=market, quantity=quantity, avg_cost=avg_cost, buy_date=buy_date)
                            _sync_sqlite_user_data(current_user)
                            note = f"已保存持仓 {symbol}。"
                elif mode == "holding_remove":
                    if not current_user:
                        error = "请先登录后再管理持仓。"
                    else:
                        market = _normalize_market(request.form.get("holding_market", "fund"))
                        symbol = _normalize_symbol(request.form.get("holding_symbol", ""), market)
                        if not symbol:
                            error = "缺少持仓代码。"
                        else:
                            ok = _current_holdings_mgr().remove(symbol, market=market)
                            _sync_sqlite_user_data(current_user)
                            note = f"已删除持仓 {symbol}。" if ok else f"未找到持仓 {symbol}。"
                elif mode == "alert_add":
                    if not current_user:
                        error = "请先登录后再设置价格预警。"
                    else:
                        market = _normalize_market(request.form.get("alert_market", "fund"))
                        symbol = _normalize_symbol(request.form.get("alert_symbol", ""), market)
                        target_price = _parse_bounded_float(request.form.get("alert_target_price", ""), "目标价", 0.000001, 1_000_000_000)
                        condition = request.form.get("alert_condition", "lte")
                        if condition not in {"lte", "gte"}:
                            raise ValueError("预警条件无效")
                        if not symbol or target_price <= 0:
                            error = "请输入有效的预警代码和目标价格。"
                        else:
                            alerts = _read_alerts(username=current_user)
                            alerts.insert(0, {
                                "id": uuid4().hex[:12],
                                "symbol": symbol,
                                "market": market,
                                "target_price": target_price,
                                "condition": condition,
                                "enabled": True,
                                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "last_triggered_at": "",
                            })
                            _write_alerts(alerts, username=current_user)
                            note = f"已添加 {symbol} 的价格预警。"
                elif mode == "alert_remove":
                    if not current_user:
                        error = "请先登录。"
                    else:
                        alert_id = request.form.get("alert_id", "")
                        alerts = [a for a in _read_alerts(username=current_user) if a.get("id") != alert_id]
                        _write_alerts(alerts, username=current_user)
                        note = "已删除价格预警。"
                elif mode == "alert_check":
                    if not current_user:
                        error = "请先登录。"
                    else:
                        hits = _evaluate_alerts(username=current_user)
                        note = "已检查价格预警。" if not hits else " | ".join(hits)
                elif mode == "automation_save":
                    if not current_user:
                        error = "请先登录后再配置自动化任务。"
                    else:
                        run_time = _normalize_run_time(request.form.get("automation_time", "09:00"))
                        interval_minutes = _bounded_int((request.form.get("alert_interval_minutes", "") or "15").strip(), 15, 1, 1440)
                        maintenance_minutes = _bounded_int((request.form.get("maintenance_interval_minutes", "") or "60").strip(), 60, 5, 10080)
                        automations = [
                            {"id": "daily_holdings_scan", "job_type": "daily_holdings_scan", "run_time": run_time, "enabled": request.form.get("daily_scan_enabled") == "on"},
                            {"id": "daily_digest", "job_type": "daily_digest", "run_time": run_time, "enabled": request.form.get("daily_digest_enabled") == "on"},
                            {"id": "price_alert_scan", "job_type": "price_alert_scan", "interval_minutes": interval_minutes, "enabled": request.form.get("price_scan_enabled") == "on"},
                            {"id": "system_maintenance", "job_type": "system_maintenance", "interval_minutes": maintenance_minutes, "enabled": request.form.get("maintenance_enabled") == "on"},
                        ]
                        preserved = [
                            item for item in _read_automations(username=current_user)
                            if item.get("id") not in {job["id"] for job in automations}
                        ]
                        _write_automations([*preserved, *automations], username=current_user)
                        _reload_user_jobs(current_user)
                        note = "自动化设置已保存。"
                elif mode == "automation_run":
                    if not current_user:
                        error = "请先登录。"
                    else:
                        job_types = request.form.getlist("job_type")
                        job_type = job_types[-1] if job_types else "daily_holdings_scan"
                        if job_type not in {"daily_holdings_scan", "daily_digest", "price_alert_scan", "system_maintenance", "market_daily_report", "market_weekly_report", "max_history_refresh"}:
                            job_type = "daily_holdings_scan"
                        _automation_job_runner(current_user, job_type)
                        note = f"已运行自动化任务 {job_type}。"
                else:
                    error = "Unknown request type."
            except ValueError as exc:
                error = str(exc)
            except Exception as exc:
                traceback.print_exc()
                error = _friendly_error(exc)

        notifications = _consume_notifications(current_user)
        if notifications and not note:
            note = " | ".join(item["message"] for item in notifications[:3])

        template = DASHBOARD_PAGE_TEMPLATE if module_view is None else PAGE_TEMPLATE
        return render_template_string(
            template,
            result=result,
            note=note,
            error=error,
            form=form,
            holdings=_current_holdings_mgr().list_all() if current_user else [],
            analysis_history=_read_history(username=current_user),
            alerts=_read_alerts(username=current_user),
            automations=_read_automations(username=current_user),
            automation_log=_read_automation_log(username=current_user),
            cache_count=_cache_count(),
            llm_provider=(agent.llm.provider if agent.llm else "not configured"),
            default_market=agent.config["market"]["default_market"],
            default_symbol=agent.config["market"]["default_symbol"],
            current_user=current_user,
            recent_reports=_list_recent_reports(),
            module_view=module_view,
        )
