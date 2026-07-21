"""
AI量化智能体核心
整合数据获取、指标计算、LLM分析、决策输出
"""
import sys
import yaml
import pandas as pd
from pathlib import Path

# 将父目录加入路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.console import configure_console_output
from core.data_fetcher import DataFetcher
from core.indicators import add_all_indicators, generate_signal_summary
from core.backtest import BacktestEngine
from core.fund_manager import fetch_fund_manager, format_manager_report
from core.value_analysis import fetch_stock_value, format_value_report
from agent.llm_client import LLMClient

configure_console_output()


class QuantAgent:
    """
    AI 量化智能体
    一句话描述: 自动获取数据 → 计算指标 → AI分析 → 生成决策报告
    """

    def __init__(self, config_path: str = "config.yaml", paper_trade: bool = False):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        self.data_fetcher = DataFetcher(
            source=self.config["market"]["data_source"]
        )
        self.backtest_engine = BacktestEngine(
            initial_cash=self.config["backtest"]["initial_cash"],
            commission=self.config["backtest"]["commission"],
            slippage=self.config["backtest"]["slippage"],
        )

        # 初始化大模型（优先从环境变量/.env读取，其次用config.yaml）
        llm_cfg = self.config["llm"]
        try:
            self.llm = LLMClient(
                provider=llm_cfg.get("provider", ""),
                api_key=llm_cfg.get("api_key", ""),
                base_url=llm_cfg.get("base_url", ""),
                model=llm_cfg.get("model", ""),
                temperature=llm_cfg.get("temperature", 0.3),
            )
        except ValueError:
            self.llm = None
            print("[提示] 未配置大模型 API Key，AI 分析功能将不可用。")

        # This report-only build intentionally disables paper trading.
        self.paper_trader = None

    def analyze(
        self,
        symbol: str = None,
        market: str = None,
        period: str = "max",
        use_ai: bool = True,
        force_refresh: bool = False,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict:
        """
        执行一次完整的分析流程

        返回字典包含:
            - symbol: 标的代码
            - df: 带指标的DataFrame
            - signals: 技术指标信号摘要
            - ai_report: AI分析报告（如可用）
            - backtest: 回测结果（基于简单均线策略）
        """
        symbol = symbol or self.config["market"]["default_symbol"]
        market = market or self.config["market"]["default_market"]

        print(f"\n📊 正在获取 [{market}] {symbol} 的历史数据...")
        df = self.data_fetcher.fetch(symbol, market=market, period=period, force_refresh=force_refresh)
        print(f"   获取到 {len(df)} 条 K 线数据")
        if start_date or end_date:
            if df.empty:
                raise ValueError("当前标的没有可用于区间筛选的数据。")
            filtered = df.copy()
            filtered.index = pd.to_datetime(filtered.index)
            if start_date:
                start_ts = pd.to_datetime(start_date)
                filtered = filtered[filtered.index >= start_ts]
            if end_date:
                end_ts = pd.to_datetime(end_date)
                filtered = filtered[filtered.index <= end_ts]
            if filtered.empty:
                raise ValueError("所选回测区间内没有可用行情数据，请调整开始或结束日期。")
            df = filtered
            print(f"   回测区间筛选后剩余 {len(df)} 条 K 线数据")

        # 计算技术指标
        print("📈 正在计算技术指标...")
        df = add_all_indicators(df, config=self.config.get("strategy"))
        signals = generate_signal_summary(df)

        # 打印信号摘要
        print("\n🔔 技术指标信号:")
        for k, v in signals.items():
            print(f"   {k}: {v}")

        result = {
            "symbol": symbol,
            "market": market,
            "df": df,
            "signals": signals,
            "ai_report": None,
            "backtest": None,
        }

        val_data = None
        if market in ("us_stock", "a_stock"):
            val_data = fetch_stock_value(symbol, market)

        # AI 分析
        if use_ai and self.llm:
            print("🤖 正在调用大模型分析...")
            latest_price = df["close"].iloc[-1]
            # 只给模型最近3天数据，减少提示词体积，加快网页端响应。
            recent = df.tail(3)[["open", "high", "low", "close", "volume"]].round(2)
            recent_text = recent.to_string()

            ai_report = self.llm.analyze_market(
                symbol=f"{symbol} ({market})",
                latest_price=round(latest_price, 2),
                indicators_summary=signals,
                recent_data_text=recent_text,
                fundamentals_text=self._format_fundamentals_for_ai(market, val_data),
            )
            result["ai_report"] = ai_report
            print("\n📝 AI 分析报告:")
            print(ai_report)

        # 简单回测（均线交叉策略作为示例）
        print("\n📉 正在执行示例策略回测...")
        df["signal"] = 0

        # 根据可用数据量动态选择均线（基金数据可能只有10几天）
        valid_ma = [c for c in df.columns if c.startswith("MA") and df[c].notna().sum() >= 5]
        if len(valid_ma) >= 2:
            fast_col = valid_ma[0]   # 周期最短的有数据均线
            slow_col = valid_ma[1]   # 周期次短的有数据均线
            df.loc[df[fast_col] > df[slow_col], "signal"] = 1
            df.loc[df[fast_col] <= df[slow_col], "signal"] = 0
            print(f"   均线观察规则: {fast_col} 上穿 {slow_col}，状态偏强")
        else:
            print("   数据量不足，无法生成均线信号")

        # 基金使用专门的回测模式
        if market == "fund":
            bt_engine = BacktestEngine(
                initial_cash=self.config["backtest"]["initial_cash"],
                fund_mode=True,
                subscribe_fee=self.config.get("fund", {}).get("subscribe_fee", 0.001),
            )
            print("💰 基金回测模式（含申购赎回费）")
        else:
            bt_engine = self.backtest_engine

        bt_result = bt_engine.run(df, signal_col="signal")
        result["backtest"] = bt_result
        print(bt_result.summary)

        # 买入持有基准对比
        benchmark = bt_engine.benchmark_buy_and_hold(df)
        result["benchmark"] = benchmark
        print(f"📌 同期买入持有收益: {benchmark.total_return*100:.2f}%")

        # 基金经理信息（仅限场外基金）
        if market == "fund":
            mgr_data = fetch_fund_manager(symbol)
            if mgr_data:
                mgr_report = format_manager_report(mgr_data)
                if mgr_report:
                    print(mgr_report)

        # 价值分析（股票/基金）
        if market in ("us_stock", "a_stock", "fund"):
            if val_data is None:
                val_data = fetch_stock_value(symbol, market)
            if val_data:
                val_report = format_value_report(val_data)
                if val_report:
                    print(val_report)
            else:
                print("\n⚠️ 价值分析数据获取失败（可能是网络限制）")
                if market in ("us_stock", "a_stock"):
                    print(format_value_report({
                        "market": market,
                        "symbol": symbol,
                        "name": symbol,
                    }))

        print(self._format_cross_asset_valuation(market, val_data))

        # 观察信号与风险复核口径
        signal = self.generate_trade_signal(df)
        current_position = 0
        action = "observe_strong" if signal == 1 else "observe_risk" if signal == -1 else "observe_neutral"
        print(f"\n💡 程序观察信号: {signal} ({action})")

        # 复核融合：程序观察信号 + AI观察信号 + 风控 → 观察结论
        final_decision = self._fusion_decision(
            symbol=symbol,
            program_signal=signal,
            ai_report=result.get("ai_report"),
            current_position=current_position,
        )
        print("\n" + "=" * 50)
        print("🎯 【复盘观察结论】")
        print("=" * 50)
        print(f"  标的: {final_decision['标的']}")
        print(f"  程序观察: {'偏强' if final_decision['程序信号']==1 else ('偏弱' if final_decision['程序信号']==-1 else '中性')}")
        print(f"  AI观察: {'偏强' if final_decision['AI信号']==1 else ('偏弱' if final_decision['AI信号']==-1 else '中性')}")
        print(f"  风控状态: {final_decision['风控状态']}")
        print(f"  信心度: {final_decision['信心度']}")
        print(f"  观察结论: {final_decision['操作建议']}")
        print("=" * 50)

        result["valuation"] = val_data or {}
        return result

    def _format_fundamentals_for_ai(self, market: str, val_data=None) -> str:
        if market not in ("us_stock", "a_stock"):
            return ""
        if not val_data:
            return "股票基本面接口暂未返回可靠数据；报告中请提示用户补充年报/财报数据。"

        parts = []
        for label, key in (
            ("公司", "name"),
            ("行业", "industry"),
            ("板块", "sector"),
            ("收入", "revenue"),
            ("净利润", "net_income"),
            ("经营现金流", "operating_cashflow"),
            ("自由现金流", "free_cashflow"),
            ("PE", "pe_trailing"),
            ("PE", "pe"),
            ("PB", "pb"),
            ("ROE", "roe"),
            ("营收增长", "revenue_growth"),
            ("净利率", "profit_margin"),
        ):
            value = val_data.get(key)
            if value not in (None, "", "-"):
                parts.append(f"{label}: {value}")
        note = val_data.get("description")
        if note:
            parts.append(f"营业模式: {' '.join(str(note).split())[:180]}")
        return "\n".join(parts[:12])

    def _format_cross_asset_valuation(self, market: str, val_data=None) -> str:
        """输出股票/债券/地产/收购之间可横向比较的收益率与倍数。"""
        pe = None
        fcf_multiple = None
        if val_data:
            pe = val_data.get("pe_trailing") or val_data.get("pe_forward") or val_data.get("pe")
            market_cap = val_data.get("market_cap")
            free_cashflow = val_data.get("free_cashflow")
            try:
                if market_cap and free_cashflow and float(free_cashflow) > 0:
                    fcf_multiple = float(market_cap) / float(free_cashflow)
            except Exception:
                fcf_multiple = None

        try:
            pe_float = float(pe) if pe not in (None, "", "-") else None
        except Exception:
            pe_float = None

        if pe_float and pe_float > 0:
            earning_yield = 1 / pe_float
            stock_line = f"股票收益率 E/P: {earning_yield * 100:.2f}%（由 P/E {pe_float:.2f} 倒推）"
        elif market in ("a_stock", "us_stock"):
            stock_line = "股票收益率 E/P: 暂无可靠 P/E，无法倒推；可用 每股收益 ÷ 股价 计算。"
        elif market == "fund":
            stock_line = "股票收益率 E/P: 基金本身没有单一 P/E，可参考底层持仓股票的加权盈利收益率。"
        else:
            stock_line = "股票收益率 E/P: 不适用于当前市场；用于和债券、地产、收购现金流横向比较。"

        if fcf_multiple:
            fcf_yield = 1 / fcf_multiple
            acquisition_line = f"收购现金流倍数 EV/FCF: 约 {fcf_multiple:.1f} 倍（对应现金流收益率约 {fcf_yield * 100:.2f}%）"
        elif market in ("a_stock", "us_stock"):
            acquisition_line = "收购现金流倍数 EV/FCF: 暂无完整企业价值/自由现金流；公式为 企业价值 ÷ 自由现金流。"
        else:
            acquisition_line = "收购现金流倍数 EV/FCF: 主要用于企业收购估值；倍数越高，对增长和融资环境要求越高。"

        return (
            "\n🧭 跨资产估值参照:\n"
            f"   {stock_line}\n"
            "   债券收益率 YTM: 可视为利率锚；债券收益率上升时，股票、地产和收购倍数通常承压。\n"
            "   房地产资本化率 Cap Rate: 净经营收入 ÷ 房产价格；越低代表市场愿意为租金现金流付更高价格。\n"
            f"   {acquisition_line}\n"
            "   快速换算: 10倍现金流≈10%收益率，20倍≈5%，33倍≈3%。"
        )

    def _fusion_decision(self, symbol: str, program_signal: int, ai_report: str, current_position: int) -> dict:
        """
        观察信号融合引擎
        整合程序信号 + AI信号 → 输出复盘观察结论
        """
        # 1. 解析 AI 信号
        ai_signal = 0  # 默认观望
        if ai_report:
            if "信号: 买入" in ai_report or "信号：买入" in ai_report:
                ai_signal = 1
            elif "信号: 卖出" in ai_report or "信号：卖出" in ai_report:
                ai_signal = -1

        # 2. 风控检查（如果有模拟盘）
        risk_status = "正常"
        if self.paper_trader:
            alerts = self.paper_trader.risk.check_portfolio_risk(self.paper_trader.portfolio)
            if alerts:
                risk_status = "告警"
            if self.paper_trader.risk.is_halted:
                risk_status = "暂停"

        # 3. 融合规则
        score = program_signal + ai_signal  # 范围: -2 ~ +2

        if risk_status == "暂停":
            final_signal = 0
            confidence = "极低"
            advice = "【风险预警】风控触发暂停，应先复核回撤、仓位和数据来源"
        elif score >= 2:
            final_signal = 0
            confidence = "高"
            advice = "【偏强观察】程序和 AI 均显示状态较强，可加入观察清单并复核风险"
        elif score == 1:
            final_signal = 0
            confidence = "中"
            advice = "【继续观察】单方偏强，先复核数据、回撤和持仓暴露"
        elif score == 0:
            final_signal = 0
            confidence = "低"
            if program_signal == 1 and ai_signal == -1:
                advice = "【冲突观察】程序偏强但 AI 偏弱，暂不下结论，等待更多数据验证"
            elif program_signal == -1 and ai_signal == 1:
                advice = "【冲突观察】程序偏弱但 AI 偏强，暂不下结论，等待更多数据验证"
            else:
                advice = "【中性观察】方向不明，维持复盘跟踪"
        elif score == -1:
            final_signal = 0
            confidence = "中"
            advice = "【风险复核】单方偏弱，复核回撤是否扩大和仓位是否过重"
        else:  # score <= -2
            final_signal = 0
            confidence = "高"
            advice = "【高风险观察】程序和 AI 均偏弱，应重点复核风险承受能力和集中度"

        return {
            "标的": symbol,
            "程序信号": program_signal,
            "AI信号": ai_signal,
            "融合得分": score,
            "风控状态": risk_status,
            "执行信号": final_signal,
            "信心度": confidence,
            "操作建议": advice,
        }

    def _execute_paper_trade(self, symbol: str, signal: int, price: float):
        """Trade execution is intentionally disabled in this report-only build."""
        return None

    def generate_trade_signal(self, df: pd.DataFrame) -> int:
        """
        基于多指标合成，生成观察信号
        返回: 1(偏强), 0(中性), -1(偏弱)
        """
        latest = df.iloc[-1]
        score = 0

        # 均线
        if latest.get("MA10", 0) > latest.get("MA30", 0):
            score += 1
        else:
            score -= 1

        # MACD
        if latest.get("MACD", 0) > latest.get("MACD_Signal", 0):
            score += 1
        else:
            score -= 1

        # RSI
        rsi = latest.get("RSI", 50)
        if rsi < 30:
            score += 2  # 超卖，强烈看多
        elif rsi > 70:
            score -= 2  # 超买，强烈看空
        elif rsi < 45:
            score += 1
        elif rsi > 55:
            score -= 1

        # 布林带
        close = latest["close"]
        if close < latest.get("BB_Lower", 0):
            score += 1
        elif close > latest.get("BB_Upper", 0):
            score -= 1

        if score >= 2:
            return 1
        elif score <= -2:
            return 0  # 这里用0表示空仓（A股不方便做空）
        return 0  # 观望
