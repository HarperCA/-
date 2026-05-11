"""
价值分析模块
支持美股(yfinance)、A股(akshare)和基金(东方财富 pingzhongdata)的分析
包含: 估值指标、公司背景、现金流、资产负债、基金画像
"""
from typing import Dict, Optional
import json
import re
import pandas as pd


def _to_float(value):
    """尽量把接口返回值转成 float，失败则返回 None。"""
    if value in (None, "", "-", "--"):
        return None
    try:
        if isinstance(value, str):
            value = value.replace(",", "").replace("%", "").strip()
        return float(value)
    except Exception:
        return None


def _format_amount(value) -> str:
    """格式化金额，兼容中美股不同币种口径。"""
    num = _to_float(value)
    if num is None:
        return "暂无可靠数据"
    sign = "-" if num < 0 else ""
    num = abs(num)
    if num >= 1e12:
        return f"{sign}{num / 1e12:.2f}万亿"
    if num >= 1e8:
        return f"{sign}{num / 1e8:.2f}亿"
    if num >= 1e4:
        return f"{sign}{num / 1e4:.2f}万"
    return f"{sign}{num:.2f}"


def _format_pct(value) -> str:
    num = _to_float(value)
    if num is None:
        return "暂无可靠数据"
    if abs(num) < 1:
        num *= 100
    return f"{num:.2f}%"


def _format_ratio(value) -> str:
    num = _to_float(value)
    return "暂无可靠数据" if num is None else f"{num:.2f}"


def _business_model_note(data: Dict) -> str:
    """根据已有公司描述和行业信息生成保守的经营模式摘要。"""
    description = (data.get("description") or "").strip()
    if description:
        compact = " ".join(description.split())
        return compact[:220] + ("..." if len(compact) > 220 else "")

    sector = str(data.get("sector") or data.get("industry") or "")
    if any(key in sector for key in ("银行", "金融", "保险", "Financial", "Bank")):
        return "主要通过利差、手续费、资产管理或金融服务获取收入，重点关注资产质量、资本充足率和利率周期。"
    if any(key in sector for key in ("医药", "医疗", "Healthcare", "Biotech", "Pharma")):
        return "主要依靠产品管线、研发转化、专利/准入和销售渠道变现，重点关注研发投入、毛利率和政策风险。"
    if any(key in sector for key in ("科技", "软件", "Technology", "Software", "Semiconductor")):
        return "主要依靠技术产品、平台服务、硬件或软件订阅变现，重点关注收入增长、研发效率和现金流质量。"
    if any(key in sector for key in ("消费", "零售", "Consumer", "Retail")):
        return "主要依靠品牌、渠道、周转和定价能力变现，重点关注同店增长、毛利率和库存周期。"
    if any(key in sector for key in ("能源", "材料", "Energy", "Materials")):
        return "收入和利润通常受大宗商品价格、资本开支和产能周期影响，重点关注成本曲线和资产负债表韧性。"
    return "暂无足够公开描述，建议结合年报主营业务、收入分部、客户结构和毛利率变化进一步确认。"


def _safe_get(df: pd.DataFrame, row_name: str, col_idx: int = 0):
    """从DataFrame安全提取值"""
    if df is None or df.empty or col_idx >= len(df.columns):
        return None
    col = df.columns[col_idx]
    val = df.loc.get(row_name, pd.Series()).get(col)
    return val


def fetch_us_stock_value(symbol: str) -> Optional[Dict]:
    """获取美股基本面数据 (yfinance)"""
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        info = ticker.info
        if not info:
            return None

        result = {
            "market": "us_stock",
            "symbol": symbol,
            "name": info.get("shortName", symbol),
            "sector": info.get("sector", "未知"),
            "industry": info.get("industry", "未知"),
            "country": info.get("country", "未知"),
            "employees": info.get("fullTimeEmployees"),
            "description": info.get("longBusinessSummary", ""),
            "market_cap": info.get("marketCap", 0),
            "pe_trailing": info.get("trailingPE"),
            "pe_forward": info.get("forwardPE"),
            "pb": info.get("priceToBook"),
            "ps": info.get("priceToSalesTrailing12Months"),
            "dividend_yield": info.get("dividendYield", 0),
            "roe": info.get("returnOnEquity"),
            "revenue_growth": info.get("revenueGrowth"),
            "profit_margin": info.get("profitMargins"),
            "gross_margin": info.get("grossMargins"),
            "operating_margin": info.get("operatingMargins"),
            "revenue": info.get("totalRevenue"),
            "net_income": info.get("netIncomeToCommon"),
            "ebitda": info.get("ebitda"),
            "debt_to_equity": info.get("debtToEquity"),
            "current_price": info.get("currentPrice"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
        }

        # 现金流
        try:
            cf = ticker.cashflow
            if cf is not None and not cf.empty:
                result["operating_cashflow"] = _safe_get(cf, "Operating Cash Flow")
                result["capex"] = _safe_get(cf, "Capital Expenditure")
                if result.get("operating_cashflow") and result.get("capex"):
                    result["free_cashflow"] = result["operating_cashflow"] + result["capex"]
        except Exception:
            pass

        # 资产负债
        try:
            bs = ticker.balance_sheet
            if bs is not None and not bs.empty:
                result["total_assets"] = _safe_get(bs, "Total Assets")
                result["total_liabilities"] = _safe_get(bs, "Total Liabilities Net Minority Interest")
                result["total_equity"] = _safe_get(bs, "Stockholders Equity")
                result["current_assets"] = _safe_get(bs, "Current Assets")
                result["current_liabilities"] = _safe_get(bs, "Current Liabilities")
                if result.get("current_assets") and result.get("current_liabilities"):
                    result["current_ratio"] = result["current_assets"] / result["current_liabilities"]
        except Exception:
            pass

        # 利润表补充，info 字段缺失时使用财报表格兜底
        try:
            fin = ticker.financials
            if fin is not None and not fin.empty:
                result["revenue"] = result.get("revenue") or _safe_get(fin, "Total Revenue")
                result["gross_profit"] = _safe_get(fin, "Gross Profit")
                result["operating_income"] = _safe_get(fin, "Operating Income")
                result["net_income"] = result.get("net_income") or _safe_get(fin, "Net Income")
        except Exception:
            pass

        return result
    except Exception:
        return None


def fetch_a_stock_value(symbol: str) -> Optional[Dict]:
    """获取A股基本面数据 (akshare)"""
    try:
        import akshare as ak
        # 个股指标
        df = ak.stock_financial_analysis_indicator(symbol=symbol)
        if df is None or len(df) == 0:
            return None
        latest = df.iloc[0]
        result = {
            "market": "a_stock",
            "symbol": symbol,
            "name": latest.get("股票简称", symbol),
            "pe": latest.get("市盈率"),
            "pb": latest.get("市净率"),
            "roe": latest.get("净资产收益率"),
            "dividend_yield": latest.get("股息率"),
            "revenue_growth": latest.get("营业收入同比增长率"),
            "profit_margin": latest.get("销售净利率"),
            "gross_margin": latest.get("销售毛利率"),
            "net_income_growth": latest.get("净利润同比增长率"),
            "debt_ratio": latest.get("资产负债率"),
        }

        # 公司基础信息，接口偶尔变化，失败不影响主报告
        try:
            info_df = ak.stock_individual_info_em(symbol=symbol)
            if info_df is not None and not info_df.empty:
                info = dict(zip(info_df["item"], info_df["value"]))
                result["name"] = info.get("股票简称") or info.get("股票名称") or result["name"]
                result["industry"] = info.get("行业") or result.get("industry")
                result["market_cap"] = _to_float(info.get("总市值"))
                result["current_price"] = _to_float(info.get("最新"))
                result["listing_date"] = info.get("上市时间")
        except Exception:
            pass

        return result
    except Exception:
        return None


def fetch_fund_value(symbol: str) -> Optional[Dict]:
    """获取基金画像与价值分析数据 (东方财富 pingzhongdata)"""
    try:
        import requests

        url = f"https://fund.eastmoney.com/pingzhongdata/{symbol}.js"
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})

        text = None
        for enc in ("utf-8-sig", "utf-8", "gbk", "gb2312", "gb18030"):
            try:
                decoded = resp.content.decode(enc)
                if "Data_currentFundManager" in decoded or "Data_assetAllocation" in decoded:
                    text = decoded
                    break
            except Exception:
                continue
        if not text:
            return None

        def extract_var(name: str):
            pattern = rf"var\s+{name}\s*=\s*(.*?);"
            match = re.search(pattern, text, re.S)
            if not match:
                return None
            raw = match.group(1).strip()
            try:
                return json.loads(raw)
            except Exception:
                return raw.strip("\"'")

        result = {
            "market": "fund",
            "symbol": symbol,
            "name": extract_var("fS_name") or symbol,
            "fund_type": extract_var("swithSameType"),
            "unit_nav_trend": extract_var("Data_netWorthTrend") or [],
            "asset_allocation": extract_var("Data_assetAllocation") or {},
            "holder_structure": extract_var("Data_holderStructure") or {},
            "performance_evaluation": extract_var("Data_performanceEvaluation") or {},
            "manager_data": extract_var("Data_currentFundManager") or [],
            "fund_shares_positions": extract_var("Data_fundSharesPositions") or [],
            "fluctuation_scale": extract_var("Data_fluctuationScale") or {},
            "buy_sedemption": extract_var("Data_buySedemption") or {},
            "return_1m": extract_var("syl_1y"),
            "return_3m": extract_var("syl_3y"),
            "return_6m": extract_var("syl_6y"),
            "return_1y": extract_var("syl_1n"),
            "subscribe_rate": extract_var("fund_Rate"),
            "source_rate": extract_var("fund_sourceRate"),
            "min_purchase": extract_var("fund_minsg"),
        }

        trend = result["unit_nav_trend"]
        if trend:
            latest = trend[-1]
            result["current_nav"] = latest.get("y")
            nav_values = [item.get("y") for item in trend if item.get("y") is not None]
            if nav_values:
                result["nav_high"] = max(nav_values)
                result["nav_low"] = min(nav_values)
                result["nav_position_pct"] = (
                    (result["current_nav"] - result["nav_low"]) /
                    (result["nav_high"] - result["nav_low"]) * 100
                ) if result["nav_high"] != result["nav_low"] else 100.0

        perf = result["performance_evaluation"]
        if perf and isinstance(perf, dict):
            try:
                result["performance_score"] = float(perf.get("avr"))
            except Exception:
                pass

        managers = result["manager_data"]
        if managers:
            mgr = managers[0]
            result["manager_name"] = mgr.get("name")
            result["manager_star"] = mgr.get("star")
            result["manager_work_time"] = mgr.get("workTime")
            result["manager_fund_size"] = mgr.get("fundSize")

        alloc = result["asset_allocation"]
        if alloc and isinstance(alloc, dict):
            series = alloc.get("series", [])
            if series:
                for item in series:
                    name = item.get("name", "")
                    data = item.get("data", [])
                    if not data:
                        continue
                    latest_value = data[-1]
                    if "股票占净比" in name:
                        result["stock_pct"] = latest_value
                    elif "债券占净比" in name:
                        result["bond_pct"] = latest_value
                    elif "现金占净比" in name:
                        result["cash_pct"] = latest_value
                    elif "净资产" in name:
                        result["net_assets"] = latest_value

        holders = result["holder_structure"]
        if holders and isinstance(holders, dict):
            series = holders.get("series", [])
            for item in series:
                name = item.get("name", "")
                data = item.get("data", [])
                if not data:
                    continue
                latest_value = data[-1]
                if "机构持有比例" in name:
                    result["institutional_holders_pct"] = latest_value
                elif "个人持有比例" in name:
                    result["retail_holders_pct"] = latest_value

        return result
    except Exception:
        return None


def evaluate_value(data: Dict) -> Dict:
    """基于基本面数据给出估值判断"""
    judgments = {}

    pe = _to_float(data.get("pe_trailing") or data.get("pe"))
    if pe is not None:
        if pe < 0:
            judgments["pe"] = "亏损"
        elif pe < 15:
            judgments["pe"] = "低估"
        elif pe < 25:
            judgments["pe"] = "合理"
        else:
            judgments["pe"] = "高估"

    pb = _to_float(data.get("pb"))
    if pb is not None:
        if pb < 1:
            judgments["pb"] = "低估"
        elif pb < 3:
            judgments["pb"] = "合理"
        else:
            judgments["pb"] = "高估"

    roe = _to_float(data.get("roe"))
    if roe is not None:
        roe_pct = roe * 100 if roe < 1 else roe  # 兼容小数和百分比
        if roe_pct > 20:
            judgments["roe"] = "优秀"
        elif roe_pct > 15:
            judgments["roe"] = "良好"
        elif roe_pct > 10:
            judgments["roe"] = "一般"
        else:
            judgments["roe"] = "较差"

    dy = _to_float(data.get("dividend_yield"))
    if dy is not None:
        dy_pct = dy * 100 if dy < 0.1 else dy
        if dy_pct > 3:
            judgments["dividend"] = "高股息"
        elif dy_pct > 1:
            judgments["dividend"] = "中等"
        else:
            judgments["dividend"] = "低股息"

    return judgments


def format_value_report(data: Optional[Dict]) -> str:
    """格式化价值分析报告"""
    if not data:
        return ""

    if data.get("market") == "fund":
        return format_fund_value_report(data)

    judgments = evaluate_value(data)
    is_stock = data.get("market") in ("us_stock", "a_stock")
    report_title = "📊 公司财务与商业模式分析" if is_stock else "📊 价值分析"
    lines = [
        "",
        "=" * 55,
        report_title,
        "=" * 55,
    ]

    # 公司背景
    lines.append(f"\n🏢 公司背景与营业模式:")
    lines.append(f"  名称: {data.get('name', data['symbol'])}")
    if data.get("sector"):
        lines.append(f"  行业: {data['sector']}")
    if data.get("industry"):
        lines.append(f"  细分: {data['industry']}")
    if data.get("country"):
        lines.append(f"  国家: {data['country']}")
    if data.get("employees"):
        lines.append(f"  员工: {data['employees']:,} 人")
    if data.get("listing_date"):
        lines.append(f"  上市时间: {data['listing_date']}")
    lines.append(f"  营业模式: {_business_model_note(data)}")

    # 市值
    if data.get("market_cap"):
        lines.append(f"  市值: {_format_amount(data['market_cap'])}")

    # 估值指标
    lines.append("\n💰 估值指标:")
    pe = data.get("pe_trailing") or data.get("pe")
    if pe is not None:
        j = judgments.get("pe", "")
        lines.append(f"    市盈率(PE): {_format_ratio(pe)} [{j}]")
        pe_num = _to_float(pe)
        if pe_num and pe_num > 0:
            lines.append(f"    股票收益率(E/P): {100 / pe_num:.2f}%")
    else:
        lines.append("    市盈率(PE): 暂无可靠数据")
    pb = data.get("pb")
    if pb is not None:
        j = judgments.get("pb", "")
        lines.append(f"    市净率(PB): {_format_ratio(pb)} [{j}]")
    ps = data.get("ps")
    if ps is not None:
        lines.append(f"    市销率(PS): {_format_ratio(ps)}")

    # 资产与负债
    lines.append("\n📈 资产负债:")
    ta = data.get("total_assets")
    if ta is not None:
        lines.append(f"    总资产: {_format_amount(ta)}")
    tl = data.get("total_liabilities")
    if tl is not None:
        lines.append(f"    总负债: {_format_amount(tl)}")
    te = data.get("total_equity")
    if te is not None:
        lines.append(f"    股东权益: {_format_amount(te)}")
    cr = data.get("current_ratio")
    if cr is not None:
        lines.append(f"    流动比率: {_format_ratio(cr)}")
    de = data.get("debt_to_equity")
    if de is not None:
        lines.append(f"    负债权益比: {_format_ratio(de)}")
    debt_ratio = data.get("debt_ratio")
    if debt_ratio is not None:
        lines.append(f"    资产负债率: {_format_pct(debt_ratio)}")
    if all(data.get(k) is None for k in ("total_assets", "total_liabilities", "total_equity", "current_ratio", "debt_to_equity", "debt_ratio")):
        lines.append("    暂无可靠资产负债表数据")

    # 现金流
    lines.append("\n💵 现金流:")
    ocf = data.get("operating_cashflow")
    if ocf is not None:
        lines.append(f"    经营现金流: {_format_amount(ocf)}")
    fcf = data.get("free_cashflow")
    if fcf is not None:
        lines.append(f"    自由现金流: {_format_amount(fcf)}")
    capex = data.get("capex")
    if capex is not None:
        lines.append(f"    资本支出: {_format_amount(capex)}")
    if all(data.get(k) is None for k in ("operating_cashflow", "free_cashflow", "capex")):
        lines.append("    暂无可靠现金流数据；建议补充年报现金流量表后再判断现金质量。")

    # 质量指标
    lines.append("\n🎯 收入与盈利能力:")
    revenue = data.get("revenue")
    if revenue is not None:
        lines.append(f"    营业收入: {_format_amount(revenue)}")
    gross_profit = data.get("gross_profit")
    if gross_profit is not None:
        lines.append(f"    毛利润: {_format_amount(gross_profit)}")
    operating_income = data.get("operating_income")
    if operating_income is not None:
        lines.append(f"    营业利润: {_format_amount(operating_income)}")
    net_income = data.get("net_income")
    if net_income is not None:
        lines.append(f"    净利润: {_format_amount(net_income)}")
    roe = data.get("roe")
    if roe is not None:
        j = judgments.get("roe", "")
        lines.append(f"    ROE: {_format_pct(roe)} [{j}]")
    dy = data.get("dividend_yield")
    if dy is not None:
        j = judgments.get("dividend", "")
        lines.append(f"    股息率: {_format_pct(dy)} [{j}]")
    rg = data.get("revenue_growth")
    if rg is not None:
        lines.append(f"    营收增长: {_format_pct(rg)}")
    nig = data.get("net_income_growth")
    if nig is not None:
        lines.append(f"    净利润增长: {_format_pct(nig)}")
    gm = data.get("gross_margin")
    if gm is not None:
        lines.append(f"    毛利率: {_format_pct(gm)}")
    pm = data.get("profit_margin")
    if pm is not None:
        lines.append(f"    净利率: {_format_pct(pm)}")
    om = data.get("operating_margin")
    if om is not None:
        lines.append(f"    营业利润率: {_format_pct(om)}")
    if all(data.get(k) is None for k in ("revenue", "net_income", "roe", "revenue_growth", "profit_margin", "gross_margin", "operating_margin")):
        lines.append("    暂无可靠利润表数据")

    if is_stock:
        lines.append("\n🧾 财务质量检查:")
        fcf_num = _to_float(data.get("free_cashflow"))
        ni_num = _to_float(data.get("net_income"))
        if fcf_num is not None and ni_num is not None:
            cash_conversion = fcf_num / ni_num if ni_num else None
            if cash_conversion is not None:
                lines.append(f"    自由现金流/净利润: {cash_conversion:.2f}")
        elif fcf_num is not None:
            lines.append("    自由现金流已披露，但净利润缺失，暂不能计算现金转化率。")
        else:
            lines.append("    现金转化率: 暂无可靠数据")
        if _to_float(data.get("debt_ratio")) is not None or _to_float(data.get("debt_to_equity")) is not None:
            lines.append("    杠杆观察: 已列出债务/资产负债相关指标，需结合利率环境和行业周期判断。")
        else:
            lines.append("    杠杆观察: 暂无可靠杠杆数据。")

    # 价格位置
    cp = data.get("current_price")
    h52 = data.get("fifty_two_week_high")
    l52 = data.get("fifty_two_week_low")
    if cp and h52 and l52:
        position = (cp - l52) / (h52 - l52) * 100
        lines.append(f"\n📍 价格位置: {position:.1f}% (52周高低区间)")

    lines.append("=" * 55)
    return "\n".join(lines)


def format_fund_value_report(data: Optional[Dict]) -> str:
    """格式化基金价值分析报告"""
    if not data:
        return ""

    lines = [
        "",
        "=" * 55,
        "📊 基金价值分析",
        "=" * 55,
        "",
        "🏷️ 基金概况:",
        f"  名称: {data.get('name', data['symbol'])}",
        f"  代码: {data.get('symbol', '')}",
    ]

    current_nav = data.get("current_nav")
    if current_nav is not None:
        lines.append(f"  最新单位净值: {current_nav:.4f}")
    if data.get("min_purchase"):
        lines.append(f"  最低申购: {data['min_purchase']}")
    if data.get("subscribe_rate") is not None:
        lines.append(f"  当前申购费率: {data['subscribe_rate']}")
    if data.get("source_rate") is not None:
        lines.append(f"  原始申购费率: {data['source_rate']}")

    lines.append("\n📈 收益概览:")
    for label, key in (("近1月", "return_1m"), ("近3月", "return_3m"), ("近6月", "return_6m"), ("近1年", "return_1y")):
        value = data.get(key)
        if value not in (None, ""):
            lines.append(f"  {label}: {value}%")

    lines.append("\n🎯 综合画像:")
    if data.get("performance_score") is not None:
        lines.append(f"  综合评分: {data['performance_score']:.2f}")
    if data.get("nav_position_pct") is not None:
        lines.append(f"  净值位置: {data['nav_position_pct']:.1f}% (历史区间)")
    if data.get("manager_name"):
        lines.append(f"  基金经理: {data['manager_name']}")
    if data.get("manager_work_time"):
        lines.append(f"  任职时长: {data['manager_work_time']}")
    if data.get("manager_star"):
        lines.append(f"  经理评级: {'⭐' * int(data['manager_star'])}")
    if data.get("manager_fund_size"):
        lines.append(f"  管理规模: {data['manager_fund_size']}")

    lines.append("\n🧱 资产配置:")
    if data.get("stock_pct") is not None:
        lines.append(f"  股票占比: {data['stock_pct']:.2f}%")
    if data.get("bond_pct") is not None:
        lines.append(f"  债券占比: {data['bond_pct']:.2f}%")
    if data.get("cash_pct") is not None:
        lines.append(f"  现金占比: {data['cash_pct']:.2f}%")
    if data.get("net_assets") is not None:
        lines.append(f"  净资产: {data['net_assets']:.2f} 亿")

    lines.append("\n👥 持有人结构:")
    if data.get("institutional_holders_pct") is not None:
        lines.append(f"  机构持有: {data['institutional_holders_pct']:.2f}%")
    if data.get("retail_holders_pct") is not None:
        lines.append(f"  个人持有: {data['retail_holders_pct']:.2f}%")

    lines.append("\n💡 解读:")
    score = data.get("performance_score")
    nav_pos = data.get("nav_position_pct")
    stock_pct = data.get("stock_pct")
    if score is not None:
        if score >= 85:
            lines.append("  综合评价偏强，历史表现与管理能力较突出")
        elif score >= 70:
            lines.append("  综合评价中上，属于相对均衡的基金")
        else:
            lines.append("  综合评价一般，需更重视波动和回撤")
    if nav_pos is not None:
        if nav_pos >= 80:
            lines.append("  当前净值接近历史高位，追高需要更谨慎")
        elif nav_pos <= 20:
            lines.append("  当前净值处于历史低位，需结合趋势判断是否左侧布局")
    if stock_pct is not None:
        if stock_pct >= 80:
            lines.append("  权益仓位较高，净值弹性更强，但回撤也会更明显")
        elif stock_pct <= 30:
            lines.append("  权益仓位较低，波动通常相对温和")

    lines.append("=" * 55)
    return "\n".join(lines)


def fetch_stock_value(symbol: str, market: str) -> Optional[Dict]:
    """统一入口：根据市场类型获取价值数据"""
    if market == "us_stock":
        return fetch_us_stock_value(symbol)
    elif market == "a_stock":
        return fetch_a_stock_value(symbol)
    elif market == "fund":
        return fetch_fund_value(symbol)
    return None
