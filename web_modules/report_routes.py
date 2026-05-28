# -*- coding: utf-8 -*-
from __future__ import annotations

import io
import json
import re
from pathlib import Path
from uuid import uuid4

import pandas as pd
from flask import jsonify, redirect, render_template_string, request, send_file, url_for

from web_modules.research_report import (
    build_report_from_analysis,
    build_report_from_upload,
    read_uploaded_table,
    save_report_bundle,
)
from web_modules.source_records import apply_data_breadth, record, upload_source_record
from web_modules.templates import RESEARCH_REPORT_PAGE_TEMPLATE


REPORT_TYPES = {
    "个人持仓体检报告",
    "基金/ETF 分析报告",
    "小资金组合风险报告",
    "交易复盘报告",
    "亏损原因分析报告",
    "定投/补仓观察报告",
    "每周账户复盘报告",
}
AUDIENCES = {"个人投资者版", "小资金账户版", "业余量化版", "小型投研团队版"}
DATA_BREADTHS = {"基础", "标准", "深度"}


def register_report_routes(app, deps: dict) -> None:
    current_user = deps["current_user"]
    ensure_user_space = deps["ensure_user_space"]
    user_dir = deps["user_dir"]
    safe_username = deps["safe_username"]
    friendly_error = deps["friendly_error"]
    read_history = deps.get("read_history")
    agent = deps.get("agent")

    def reports_dir(username: str) -> Path:
        path = user_dir(username) / "research_reports"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def uploads_dir(username: str) -> Path:
        path = user_dir(username) / "uploads"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def read_reports(username: str, limit: int = 20) -> list[dict]:
        items = []
        for path in sorted(reports_dir(username).glob("research_*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                items.append(json.loads(path.read_text(encoding="utf-8")))
            except Exception:
                continue
            if len(items) >= limit:
                break
        return items

    def report_options() -> dict:
        report_type = request.form.get("report_type", "个人持仓体检报告")
        audience = request.form.get("audience", "个人投资者版")
        data_breadth = request.form.get("data_breadth", "标准")
        objective = (request.form.get("objective") or "").strip()
        if report_type not in REPORT_TYPES:
            report_type = "个人持仓体检报告"
        if audience not in AUDIENCES:
            audience = "个人投资者版"
        if data_breadth not in DATA_BREADTHS:
            data_breadth = "标准"
        return {
            "report_type": report_type,
            "audience": audience,
            "data_breadth": data_breadth,
            "objective": objective or "看清过去表现、主要风险、持仓集中度和下一步需要观察的事项。",
        }

    def enrich_sources(base_sources: list, options: dict, username: str, **kwargs) -> list:
        return apply_data_breadth(
            base_sources,
            breadth=options.get("data_breadth", "标准"),
            user_path=user_dir(username),
            reports_path=reports_dir(username),
            db_path=Path("data/quant_app.sqlite"),
            cache_dir=Path("data/cache"),
            **kwargs,
        )

    def sample_nav_frame() -> pd.DataFrame:
        dates = pd.date_range("2025-01-02", periods=180, freq="B")
        nav = 1.0
        values = []
        for i, _date in enumerate(dates):
            if i < 80:
                nav *= 1.0018
            elif i < 115:
                nav *= 0.996
            else:
                nav *= 1.0011
            values.append(round(nav, 6))
        return pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "nav": values})

    def chat_file(username: str) -> Path:
        return user_dir(username) / "report_followups.json"

    def read_followups(username: str) -> list[dict]:
        path = chat_file(username)
        if not path.exists():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def write_followups(username: str, rows: list[dict]) -> None:
        chat_file(username).write_text(json.dumps(rows[:50], ensure_ascii=False, indent=2), encoding="utf-8")

    def fallback_followup_answer(question: str, context: str) -> str:
        text = f"{question}\n{context}"
        if any(key in text for key in ("风险", "回撤", "亏损", "波动", "继续跌")):
            return "可以继续追问。建议重点复核最大回撤、继续下跌时的可承受亏损、单一持仓集中度和交易记录完整性。这里仍保持观察和复核口径，不输出买卖指令。"
        if any(key in text for key in ("摘要", "简短", "速读")):
            return "速读版：这份报告用于看清过去表现和风险暴露。下一步应补齐数据、复核集中度、观察回撤是否扩大，不能把它写成直接买卖建议。"
        if any(key in text for key in ("客户", "交付", "改写")):
            return "展示版：本报告用于投资复盘和风险识别，展示数据来源、表现变化、回撤风险和后续观察清单，不构成投资建议。"
        return "可以继续追问。当前最值得追问的是：数据是否完整、亏损可能来自哪里、持仓是否过于集中、后续应该观察哪些信号。"

    def answer_followup(question: str, context: str, history: list[dict]) -> str:
        if agent and getattr(agent, "llm", None):
            recent = "\n".join(
                f"用户：{item.get('question', '')}\nAgent：{item.get('answer', '')}"
                for item in reversed(history[:6])
            )
            system_prompt = (
                "你是面向个人投资者和小资金用户的 AI 投资复盘与风险报告助手。"
                "请围绕报告上下文回答用户追问，重点解释表现、风险、集中度、数据缺口和下一步观察清单。"
                "使用观察、复核、验证、预警、降低仓位暴露、补充数据等谨慎口径，不能输出交易执行指令。"
            )
            user_prompt = f"报告上下文：\n{context[:3000]}\n\n最近追问：\n{recent[:1500]}\n\n用户问题：{question}"
            try:
                return agent.llm.chat(system_prompt, user_prompt).strip()
            except Exception:
                app.logger.exception("report followup llm failed")
        return fallback_followup_answer(question, context)

    @app.route("/research_report", methods=["GET", "POST"])
    def research_report_page():
        username = current_user()
        if not username:
            return redirect(url_for("login"))
        ensure_user_space(username)
        note = None
        error = None
        if request.method == "POST":
            try:
                file = request.files.get("data_file")
                if not file or not file.filename:
                    raise ValueError("请上传 CSV 或 Excel 文件")
                suffix = Path(file.filename).suffix.lower()
                if suffix not in {".csv", ".xlsx", ".xls"}:
                    raise ValueError("仅支持 CSV / Excel 文件")
                upload_path = uploads_dir(username) / f"{safe_username(username)}_{uuid4().hex[:10]}{suffix}"
                file.save(upload_path)
                df = read_uploaded_table(upload_path)
                options = report_options()
                sources = enrich_sources([upload_source_record(upload_path, df, file.filename)], options, username)
                report = build_report_from_upload(df, file.filename, options=options, source_records=sources)
                save_report_bundle(report, reports_dir(username))
                note = "投资复盘报告已生成，已补充数据来源、风险解释、持仓问题和下一步观察清单。"
            except Exception as exc:
                app.logger.exception("research report upload failed")
                error = friendly_error(exc)
        reports = read_reports(username)
        history = read_history(username=username, limit=20) if read_history else []
        return render_template_string(
            RESEARCH_REPORT_PAGE_TEMPLATE,
            reports=reports,
            latest=reports[0] if reports else None,
            history=history,
            current_user=username,
            note=note,
            error=error,
        )

    @app.route("/research_report/sample", methods=["POST"])
    def create_sample_research_report():
        username = current_user()
        if not username:
            return redirect(url_for("login"))
        ensure_user_space(username)
        df = sample_nav_frame()
        options = report_options()
        sources = enrich_sources(
            [
                record(
                    "user_upload",
                    "系统示例数据",
                    "示例净值曲线.csv",
                    fields=list(df.columns),
                    used_for="演示收益、回撤和风险报告生成流程",
                    reliability="medium",
                    notes="由系统生成的演示数据，不代表真实标的。",
                )
            ],
            options,
            username,
        )
        report = build_report_from_upload(df, "示例净值曲线.csv", options=options, source_records=sources)
        save_report_bundle(report, reports_dir(username))
        return redirect(url_for("research_report_page"))

    @app.route("/research_report/template.csv")
    def download_research_template():
        template = (
            "date,nav,return,symbol,quantity,avg_cost,weight,pnl\n"
            "2025-01-02,1.0000,,000300.SH,,,,\n"
            "2025-01-03,1.0021,,000300.SH,,,,\n"
        )
        buffer = io.BytesIO(template.encode("utf-8-sig"))
        return send_file(buffer, as_attachment=True, download_name="investment_review_template.csv", mimetype="text/csv")

    @app.route("/research_report/<report_id>.<fmt>")
    def download_research_report(report_id: str, fmt: str):
        username = current_user()
        if not username:
            return redirect(url_for("login"))
        if fmt not in {"md", "pdf", "docx"}:
            return "Not found", 404
        path = reports_dir(username) / f"{report_id}.{fmt}"
        if not path.exists() or reports_dir(username).resolve() not in path.resolve().parents:
            return "Not found", 404
        return send_file(path, as_attachment=True)

    @app.route("/api/report_followup", methods=["POST"])
    def report_followup_api():
        username = current_user()
        if not username:
            return jsonify({"ok": False, "error": "请先登录后再追问。"}), 401
        question = (request.form.get("question") or "").strip()
        context = (request.form.get("context") or "").strip()
        report_id = (request.form.get("report_id") or "").strip()
        if not question:
            return jsonify({"ok": False, "error": "请输入追问内容。"}), 400
        if len(question) > 500:
            return jsonify({"ok": False, "error": "追问内容过长，请压缩到 500 字以内。"}), 400
        if len(context) > 10000:
            return jsonify({"ok": False, "error": "上下文过长，请缩短后再追问。"}), 400
        if report_id and not re.fullmatch(r"[0-9A-Za-z_-]{1,80}", report_id):
            return jsonify({"ok": False, "error": "报告 ID 无效。"}), 400
        if report_id and not context:
            report_path = reports_dir(username) / f"{report_id}.json"
            if report_path.exists() and reports_dir(username).resolve() in report_path.resolve().parents:
                try:
                    report = json.loads(report_path.read_text(encoding="utf-8"))
                    context = report.get("markdown") or json.dumps(report.get("sections", {}), ensure_ascii=False)
                except Exception:
                    context = ""
        context = context or "用户正在查看投资复盘与风险报告。"
        history = read_followups(username)
        answer = answer_followup(question, context, history)
        row = {"question": question, "answer": answer, "context": context[:1000], "report_id": report_id}
        history.insert(0, row)
        write_followups(username, history)
        return jsonify({"ok": True, "answer": answer, "history": history[:10]})

    @app.route("/research_report/from_history/<int:item_index>.<fmt>")
    def download_history_research_report(item_index: int, fmt: str):
        username = current_user()
        if not username:
            return redirect(url_for("login"))
        if fmt not in {"md", "pdf", "docx"} or not read_history:
            return "Not found", 404
        history = read_history(username=username, limit=200)
        if item_index < 0 or item_index >= len(history):
            return "Not found", 404
        item = history[item_index]
        options = {"data_breadth": "标准"}
        sources = enrich_sources(
            [
                record(
                    "analysis_history",
                    "用户历史分析",
                    f"{item.get('symbol', '历史分析')} 分析记录",
                    fields=list(item.keys()),
                    used_for="从历史分析生成复盘报告",
                    reliability="medium",
                    notes="来源于用户历史分析记录。",
                )
            ],
            options,
            username,
            symbol=item.get("symbol"),
            market=item.get("market"),
            period=item.get("period"),
            data_range=item.get("data_range"),
        )
        report = build_report_from_analysis(item, source="history", options=options, source_records=sources)
        paths = save_report_bundle(report, reports_dir(username))
        return send_file(paths[fmt], as_attachment=True)
