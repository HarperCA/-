#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 量化智能体 - 主入口
运行方式:
    python main.py --symbol AAPL --market us_stock --paper-trade
    python main.py -i --paper-trade
"""
import argparse
import re
import yaml
from pathlib import Path

from core.console import configure_console_output

configure_console_output()

from agent.quant_agent import QuantAgent
from reports.visualizer import ReportVisualizer
from trading.order import OrderSide
from core.holdings_manager import HoldingsManager, Holding
from core.indicators import add_all_indicators, generate_signal_summary


def print_banner():
    print("=" * 60)
    print("    🤖 AI 量化智能体 v1.0")
    print("    功能: 数据获取 → 技术指标 → AI分析 → 回测 → 模拟盘 → 风控")
    print("=" * 60)
    print("\n⚠️ 风险提示:")
    print("  • 本系统仅为分析工具，不构成任何投资建议")
    print("  • 过往回测业绩不代表未来表现，策略可能失效")
    print("  • 基金/股票投资有风险，可能亏损本金")
    print("  • 请独立判断，自主决策，盈亏自负")
    print("=" * 60)


def parse_natural_language_command(text: str, agent: QuantAgent) -> dict:
    """把自然语言请求转成结构化动作，优先本地规则，再尝试 LLM。"""
    raw = text.strip()
    lowered = raw.lower()

    if lowered in ("q", "quit", "exit", "退出", "结束"):
        return {"intent": "quit"}
    if any(k in raw for k in ("持仓", "holdings")):
        return {"intent": "holdings"}
    if any(k in raw for k in ("账户", "组合", "portfolio")):
        return {"intent": "portfolio"}
    if any(k in raw for k in ("风险", "risk")):
        return {"intent": "risk"}
    if any(k in raw for k in ("情绪", "sentiment")):
        return {"intent": "sentiment"}
    if any(k in raw for k in ("报告", "图表", "report")):
        return {"intent": "report"}
    if any(k in raw for k in ("帮助", "help", "怎么用")):
        return {"intent": "help"}

    if any(k in raw for k in ("分析", "看看", "诊断", "研究")):
        symbol = ""
        market = ""
        period = "max"
        use_ai = not any(k in raw for k in ("不要ai", "不用ai", "no ai", "no-ai", "仅技术"))

        period_map = {
            "1mo": ("1mo", "1个月", "一个月", "近1月", "最近1月"),
            "3mo": ("3mo", "3个月", "三个月", "近3月", "最近3月"),
            "6mo": ("6mo", "6个月", "六个月", "半年", "近半年"),
            "1y": ("1y", "1年", "一年", "近1年", "最近1年"),
            "2y": ("2y", "2年", "两年", "近2年"),
            "5y": ("5y", "5年", "五年", "近5年"),
            "10y": ("10y", "10年", "十年", "近10年"),
            "20y": ("20y", "20年", "二十年", "近20年"),
            "50y": ("50y", "50年", "五十年", "近50年"),
            "max": ("max", "全部", "全量", "最大", "所有历史", "从有数据开始", "能有多大就多大"),
        }
        for key, aliases in period_map.items():
            if any(alias in raw for alias in aliases):
                period = key
                break

        if any(k in raw.lower() for k in ("btc", "eth", "usd", "crypto", "加密", "比特币", "以太坊")):
            market = "crypto"
        elif any(k in raw.lower() for k in ("美股", "us", "纳斯达克", "英伟达", "苹果", "特斯拉", "nvda", "aapl", "tsla")):
            market = "us_stock"
        elif "基金" in raw:
            market = "fund"
        elif "a股" in raw or "股票" in raw:
            market = "a_stock"

        code_match = re.search(r"\b[A-Z]{2,10}(?:-[A-Z]{2,10})?\b", raw.upper())
        if code_match:
            symbol = code_match.group(0)
        digit_match = re.search(r"\b\d{6}\b", raw)
        if digit_match:
            symbol = digit_match.group(0)

        if symbol:
            return {
                "intent": "analyze",
                "symbol": symbol,
                "market": market or ("fund" if symbol.isdigit() else "us_stock"),
                "period": period,
                "use_ai": use_ai,
            }

    if agent.llm:
        parsed = agent.llm.interpret_user_request(raw)
        if parsed:
            return parsed

    return {"intent": "unknown", "reply": "我没识别出你的意图。你可以直接说“分析 002982 基金”或“看看持仓”。"}


def print_agent_help():
    print("你可以直接输入自然语言，例如:")
    print("  分析 002982 基金")
    print("  看看 NVDA 近6个月")
    print("  帮我分析比特币，不要AI")
    print("  看看我的持仓")
    print("  生成图表报告")
    print("  查看风险")
    print("  退出")
    print("\n也兼容原始命令:")
    print("  analyze 002982 fund max")
    print("  holdings / portfolio / report / risk / sentiment / q")


def handle_agent_action(action: dict, agent: QuantAgent, last_result, visualizer, holdings_mgr):
    """执行结构化动作，返回新的 last_result 与是否退出。"""
    intent = (action or {}).get("intent", "")

    if intent == "quit":
        return last_result, True
    if intent == "help":
        print_agent_help()
        return last_result, False
    if intent == "holdings":
        all_h = holdings_mgr.list_all()
        if not all_h:
            print("📭 暂无持仓记录")
            return last_result, False
        print("\n请使用 `holdings` 命令查看完整诊断，或继续说“分析 002982 基金”。")
        for h in all_h:
            print(f"  - {h.symbol} ({h.market}) 数量:{h.quantity} 成本:{h.avg_cost}")
        return last_result, False
    if intent == "portfolio":
        if not agent.paper_trader:
            print("请先使用 --paper-trade 启动模拟盘")
            return last_result, False
        pt = agent.paper_trader
        print("\n📊 模拟盘账户概览")
        for k, v in pt.portfolio.to_dict().items():
            print(f"  {k}: {v}")
        return last_result, False
    if intent == "risk":
        if not agent.paper_trader:
            print("请先使用 --paper-trade 启动模拟盘")
            return last_result, False
        print("\n" + agent.paper_trader.risk.generate_risk_report(agent.paper_trader.portfolio))
        return last_result, False
    if intent == "sentiment":
        print("请使用 `sentiment` 或 `holdings` 命令查看完整情绪诊断。")
        return last_result, False
    if intent == "report":
        if last_result is None:
            print("请先分析一个标的，再生成图表。")
            return last_result, False
        df = last_result["df"]
        symbol = last_result["symbol"]
        visualizer.plot_analysis(df, symbol, save=True)
        if last_result.get("backtest"):
            bt = last_result["backtest"]
            visualizer.plot_equity_curve(bt.equity_curve, title=f"{symbol} 策略收益曲线", save=True)
        print(f"📁 已生成 {symbol} 的图表报告")
        return last_result, False
    if intent == "analyze":
        symbol = action.get("symbol")
        if not symbol:
            print(action.get("reply") or "请告诉我你想分析哪个标的，比如：分析 002982 基金")
            return last_result, False
        market = action.get("market") or "fund"
        period = action.get("period") or "max"
        use_ai = action.get("use_ai", True)
        last_result = agent.analyze(symbol=symbol, market=market, period=period, use_ai=use_ai)
        return last_result, False

    print(action.get("reply") or "我暂时没识别出这句话。你可以直接说“分析 002982 基金”。")
    return last_result, False


def interactive_mode(agent: QuantAgent):
    """交互式命令行模式（含模拟盘交易+持仓管理）"""
    print("\n进入交互模式，输入 'q' 退出")
    print("现在支持自然语言 agent 对话，你可以直接说“分析 002982 基金”或“看看我的持仓”。")
    print("分析命令:")
    print("  analyze AAPL us_stock        分析苹果股票")
    print("  analyze BTC-USD crypto 6mo   分析比特币")
    print("  mc 021662 fund               蒙特卡洛风险模拟")
    print("  sentiment                    市场情绪诊断")
    print("  notice                       查看风险提示")
    print("交易命令:")
    print("  buy AAPL 100                 买入100股")
    print("  sell AAPL 50                 卖出50股")
    print("  close AAPL                   平仓某标的")
    print("  closeall                     清仓所有")
    print("  portfolio                    查看账户持仓")
    print("  risk                         查看风控报告")
    print("  save                         保存模拟盘状态")
    print("持仓管理:")
    print("  hold 013403 fund 3000 0.85 2026-01-15  标记持仓")
    print("  unhold 013403              移除持仓")
    print("  check 013403               诊断是否该卖")
    print("  holdings                   查看所有持仓诊断")
    print("其他:")
    print("  report                       生成可视化图表")
    print("  help                         查看帮助")
    print("-" * 40)

    last_result = None
    visualizer = ReportVisualizer()
    holdings_mgr = HoldingsManager()

    while True:
        try:
            cmd = input("\n> ").strip().lower()
            if cmd in ("q", "quit", "exit"):
                break

            parts = cmd.split()
            if not parts:
                continue

            command = parts[0]

            # --- 分析命令 ---
            if command == "analyze":
                symbol = parts[1] if len(parts) > 1 else None
                market = parts[2] if len(parts) > 2 else None
                period = parts[3] if len(parts) > 3 else "max"
                if not symbol:
                    print("用法: analyze 013403 [fund] [max]")
                    print("       analyze AAPL us_stock")
                    continue
                last_result = agent.analyze(
                    symbol=symbol,
                    market=market,
                    period=period,
                    use_ai=True,
                )

            elif command == "mc":
                symbol = parts[1] if len(parts) > 1 else None
                market = parts[2] if len(parts) > 2 else "fund"
                period = parts[3] if len(parts) > 3 else "max"
                if not symbol:
                    print("用法: mc 021662 [fund] [max]")
                    continue
                try:
                    df = agent.data_fetcher.fetch(symbol, market=market, period=period)
                    if df is None or len(df) < 30:
                        print(f"❌ 数据不足，无法模拟")
                        continue
                    print(f"\n🎲 正在对 {symbol} 执行蒙特卡洛模拟...")
                    # 构建简单权益曲线（买入持有）
                    equity = (df["close"] / df["close"].iloc[0])
                    mc = agent.backtest_engine.monte_carlo(equity, n_simulations=10000, n_days=252)
                    if not mc:
                        print("❌ 模拟失败")
                        continue
                    print(f"\n{'='*60}")
                    print(f"🎲 {symbol} 蒙特卡洛模拟报告")
                    print(f"{'='*60}")
                    print(f"  历史数据: {len(df)} 天")
                    print(f"  模拟次数: {mc['n_simulations']:,} 次")
                    print(f"  模拟周期: {mc['n_days']} 个交易日")
                    print(f"\n📈 收益分布:")
                    print(f"  胜率: {mc['win_rate']*100:.1f}%")
                    print(f"  平均收益: {mc['mean_return']*100:.2f}%")
                    print(f"  中位数收益: {mc['median_return']*100:.2f}%")
                    print(f"  最好5%: {mc['p95_return']*100:.2f}%")
                    print(f"  最差5%: {mc['p5_return']*100:.2f}%")
                    print(f"  25分位: {mc['p25_return']*100:.2f}%")
                    print(f"  75分位: {mc['p75_return']*100:.2f}%")
                    print(f"\n⚠️ 回撤分布:")
                    print(f"  平均最大回撤: {mc['mean_max_dd']*100:.2f}%")
                    print(f"  最差5%回撤: {mc['p5_max_dd']*100:.2f}%")
                    print(f"  回撤超20%概率: {mc['prob_20pct_dd']*100:.1f}%")
                    print(f"  回撤超30%概率: {mc['prob_30pct_dd']*100:.1f}%")
                    print(f"{'='*60}")
                except Exception as e:
                    print(f"❌ 模拟出错: {e}")

            elif command == "notice":
                print("\n" + "=" * 60)
                print("📋 注意事项")
                print("=" * 60)
                print("⚠️ 风险提示:")
                print("  1. 本系统仅为技术分析辅助工具，不构成投资建议")
                print("  2. 过往回测业绩不代表未来表现，市场环境变化可能导致策略失效")
                print("  3. 基金/股票投资有风险，过往业绩不预示未来表现，可能亏损本金")
                print("  4. 所有数据来源于公开渠道，存在延迟、错误或被篡改的可能")
                print("  5. AI分析基于历史数据和统计规律，无法预测黑天鹅事件")
                print("\n💡 使用提示:")
                print("  • 命令前不要加 '>'，'>' 是提示符不是命令的一部分")
                print("  • 场外基金只有每日净值，没有实时价格")
                print("  • A股数据获取可能因网络问题失败")
                print("  • 建议先用 'mc' 命令了解风险分布，再考虑实盘")
                print("=" * 60)

            # --- 交易命令 ---
            elif command == "buy":
                if not agent.paper_trader:
                    print("请先使用 --paper-trade 启动模拟盘")
                    continue
                symbol = parts[1] if len(parts) > 1 else None
                if not symbol:
                    print("用法: buy 013403 [fund] 3000")
                    continue
                # 解析参数: buy 代码 [市场] 数量
                try:
                    if len(parts) >= 4:
                        # buy 013403 fund 3000
                        market = parts[2]
                        qty = int(parts[3])
                    elif len(parts) == 3:
                        # buy 013403 3000  或  buy 013403 fund
                        try:
                            qty = int(parts[2])
                            market = "fund"
                        except ValueError:
                            market = parts[2]
                            qty = 100
                    else:
                        market = "fund"
                        qty = 100
                except Exception:
                    market = "fund"
                    qty = 100

                try:
                    df = agent.data_fetcher.fetch(symbol, market=market, period="1mo")
                    price = df["close"].iloc[-1]
                    agent.paper_trader.update_prices({symbol: price})
                    agent.paper_trader.submit_order(symbol, OrderSide.BUY, qty, price=price, reason="手动买入")
                except Exception as e:
                    print(f"买入失败: {e}")

            elif command == "sell":
                if not agent.paper_trader:
                    print("请先使用 --paper-trade 启动模拟盘")
                    continue
                symbol = parts[1] if len(parts) > 1 else None
                if not symbol:
                    print("用法: sell 013403 [fund] 3000")
                    continue
                try:
                    if len(parts) >= 4:
                        market = parts[2]
                        qty = int(parts[3])
                    elif len(parts) == 3:
                        try:
                            qty = int(parts[2])
                            market = "fund"
                        except ValueError:
                            market = parts[2]
                            qty = 100
                    else:
                        market = "fund"
                        qty = 100
                except Exception:
                    market = "fund"
                    qty = 100

                try:
                    df = agent.data_fetcher.fetch(symbol, market=market, period="1mo")
                    price = df["close"].iloc[-1]
                    agent.paper_trader.update_prices({symbol: price})
                    agent.paper_trader.submit_order(symbol, OrderSide.SELL, qty, price=price, reason="手动卖出")
                except Exception as e:
                    print(f"卖出失败: {e}")

            elif command == "close":
                if not agent.paper_trader:
                    print("请先使用 --paper-trade 启动模拟盘")
                    continue
                symbol = parts[1] if len(parts) > 1 else None
                if symbol:
                    agent.paper_trader.close_position(symbol, reason="手动平仓")
                else:
                    print("用法: close AAPL")

            elif command == "closeall":
                if not agent.paper_trader:
                    print("请先使用 --paper-trade 启动模拟盘")
                    continue
                agent.paper_trader.close_all(reason="手动清仓")

            elif command == "portfolio":
                if not agent.paper_trader:
                    print("请先使用 --paper-trade 启动模拟盘")
                    continue
                pt = agent.paper_trader
                print("\n" + "=" * 50)
                print("📊 模拟盘账户概览")
                print("=" * 50)
                for k, v in pt.portfolio.to_dict().items():
                    print(f"  {k}: {v}")
                print("\n📁 当前持仓:")
                for sym, pos in pt.portfolio.positions.items():
                    if pos.quantity != 0:
                        print(f"  {sym}: {pos.quantity}股 | 成本{pos.avg_cost:.2f} | 现价{pos.current_price:.2f} | 盈亏{pos.unrealized_pnl_pct*100:.1f}%")
                if not any(p.quantity != 0 for p in pt.portfolio.positions.values()):
                    print("  (空仓)")

            elif command == "risk":
                if not agent.paper_trader:
                    print("请先使用 --paper-trade 启动模拟盘")
                    continue
                print("\n" + agent.paper_trader.risk.generate_risk_report(agent.paper_trader.portfolio))

            elif command == "save":
                if not agent.paper_trader:
                    print("请先使用 --paper-trade 启动模拟盘")
                    continue
                agent.paper_trader.save_state()
                print("💾 已保存")

            # --- 其他命令 ---
            elif command == "report":
                if last_result is None:
                    print("请先执行 analyze 命令获取数据")
                    continue
                df = last_result["df"]
                symbol = last_result["symbol"]
                visualizer.plot_analysis(df, symbol, save=True)
                if last_result.get("backtest"):
                    bt = last_result["backtest"]
                    visualizer.plot_equity_curve(bt.equity_curve, title=f"{symbol} 策略收益曲线", save=True)

            elif command == "signal":
                if last_result is None:
                    print("请先执行 analyze")
                    continue
                sig = agent.generate_trade_signal(last_result["df"])
                labels = {1: "📈 做多信号", 0: "➖ 观望", -1: "📉 做空/平仓"}
                print(f"\n当前综合信号: {labels.get(sig, '未知')}")

            # --- 持仓管理命令 ---
            elif command == "hold":
                symbol = parts[1] if len(parts) > 1 else None
                market = parts[2] if len(parts) > 2 else "fund"
                qty = float(parts[3]) if len(parts) > 3 else 0
                cost = float(parts[4]) if len(parts) > 4 else 0
                date = parts[5] if len(parts) > 5 else ""
                if symbol:
                    holdings_mgr.add(symbol, market=market, quantity=qty, avg_cost=cost, buy_date=date)
                else:
                    print("用法: hold 013403 fund 3000 0.85 2026-01-15")

            elif command == "unhold":
                symbol = parts[1] if len(parts) > 1 else None
                market = parts[2] if len(parts) > 2 else "fund"
                if symbol:
                    holdings_mgr.remove(symbol, market=market)
                else:
                    print("用法: unhold 013403")

            elif command == "check":
                symbol = parts[1] if len(parts) > 1 else None
                market = parts[2] if len(parts) > 2 else "fund"
                if not symbol:
                    print("用法: check 013403")
                    continue

                h = holdings_mgr.get(symbol, market=market)

                # 如果 holdings 里没有，去模拟盘里找
                if not h and agent.paper_trader:
                    pos = agent.paper_trader.portfolio.get_position(symbol)
                    if pos and pos.quantity > 0:
                        h = Holding(
                            symbol=symbol, market=market, quantity=pos.quantity,
                            avg_cost=pos.avg_cost, buy_date=""
                        )

                if not h:
                    print(f"❌ {symbol} 不在持仓列表中，先用 buy 或 hold 命令添加")
                    continue

                print(f"\n🔍 正在诊断 {symbol} ...")
                result = agent.analyze(symbol=symbol, market=market, period="max", use_ai=True)
                report = holdings_mgr.generate_diagnosis(
                    h, result["df"], result.get("signals", {}), result.get("ai_report", "")
                )
                print(report)

            elif command == "holdings":
                all_h = holdings_mgr.list_all()
                if not all_h:
                    print("📭 暂无持仓记录")
                    continue
                print("\n" + "=" * 50)
                print("📁 持仓列表与诊断")
                print("=" * 50)
                portfolio_data = []
                for h in all_h:
                    try:
                        df = agent.data_fetcher.fetch(h.symbol, market=h.market, period="max")
                        df = add_all_indicators(df)
                        sig = generate_signal_summary(df)
                        price = df["close"].iloc[-1]
                        pnl = (price - h.avg_cost) / h.avg_cost * 100 if h.avg_cost > 0 else 0
                        pnl_amount = (price - h.avg_cost) * h.quantity
                        ma = sig.get("均线", "")
                        macd = sig.get("MACD", "")
                        rsi_text = sig.get("RSI", "")
                        rsi_num = df["RSI"].iloc[-1] if "RSI" in df.columns else 50

                        print(f"\n▶ {h.symbol} ({h.market}) 数量:{h.quantity} 成本:{h.avg_cost:.4f} 最新:{price:.4f}")
                        print(f"   盈亏:{pnl:+.2f}% | 均线:{ma} | MACD:{macd} | RSI:{rsi_text}")

                        if pnl <= -7:
                            print("   🔴 建议: 亏损超7%，考虑止损")
                        elif pnl >= 15:
                            print("   🟡 建议: 盈利超15%，考虑止盈")
                        elif "死叉" in str(macd) and "空头" in str(ma):
                            print("   🟡 建议: 技术指标走弱，密切关注")
                        else:
                            print("   🟢 建议: 暂无卖出信号，继续持有")

                        # 收集组合报告数据
                        portfolio_data.append({
                            "symbol": h.symbol,
                            "market": h.market,
                            "quantity": h.quantity,
                            "avg_cost": h.avg_cost,
                            "current_price": price,
                            "pnl_pct": pnl,
                            "pnl_amount": pnl_amount,
                            "ma": ma,
                            "macd": macd,
                            "rsi": rsi_num,
                            "rsi_text": str(rsi_text),
                        })
                    except Exception as e:
                        print(f"\n▶ {h.symbol} 诊断失败: {e}")
                print("=" * 50)

                # 输出组合报告
                if portfolio_data:
                    report = holdings_mgr.generate_portfolio_report(portfolio_data)
                    print(report)
                    # 追加情绪诊断
                    sentiment = holdings_mgr.generate_sentiment_report(portfolio_data)
                    print(sentiment)

            elif command == "sentiment":
                all_h = holdings_mgr.list_all()
                if not all_h:
                    print("📭 暂无持仓记录，无法诊断情绪")
                    continue
                portfolio_data = []
                for h in all_h:
                    try:
                        df = agent.data_fetcher.fetch(h.symbol, h.market, "max")
                        df = add_all_indicators(df)
                        sig = generate_signal_summary(df)
                        price = df["close"].iloc[-1]
                        pnl = (price - h.avg_cost) / h.avg_cost * 100 if h.avg_cost > 0 else 0
                        pnl_amount = (price - h.avg_cost) * h.quantity
                        rsi_text = sig.get("RSI", "")
                        rsi_num = df["RSI"].iloc[-1] if "RSI" in df.columns else 50
                        portfolio_data.append({
                            "symbol": h.symbol, "market": h.market, "quantity": h.quantity,
                            "avg_cost": h.avg_cost, "current_price": price,
                            "pnl_pct": pnl, "pnl_amount": pnl_amount,
                            "ma": sig.get("均线", ""), "macd": sig.get("MACD", ""),
                            "rsi": rsi_num, "rsi_text": str(rsi_text),
                        })
                    except Exception as e:
                        print(f"▶ {h.symbol} 获取失败: {e}")
                if portfolio_data:
                    sentiment = holdings_mgr.generate_sentiment_report(portfolio_data)
                    print(sentiment)

            elif command == "help":
                print("命令:")
                print("  analyze [代码] [市场] [周期]   执行分析")
                print("  buy [代码] [数量]             模拟盘买入")
                print("  sell [代码] [数量]            模拟盘卖出")
                print("  close [代码]                  平仓")
                print("  closeall                      清仓所有")
                print("  portfolio                     查看账户")
                print("  risk                          风控报告")
                print("  save                          保存状态")
                print("  hold [代码] [市场] [数量] [成本] [日期]  添加持仓")
                print("  unhold [代码]                 移除持仓")
                print("  check [代码]                  持仓诊断")
                print("  holdings                      所有持仓")
                print("  report                        生成图表")
                print("  q                             退出")

            else:
                action = parse_natural_language_command(cmd, agent)
                last_result, should_exit = handle_agent_action(
                    action=action,
                    agent=agent,
                    last_result=last_result,
                    visualizer=visualizer,
                    holdings_mgr=holdings_mgr,
                )
                if should_exit:
                    break

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"错误: {e}")

    print("\n再见！")


def main():
    parser = argparse.ArgumentParser(description="AI 量化智能体")
    parser.add_argument("--symbol", type=str, help="标的代码，如 AAPL 或 BTC-USD")
    parser.add_argument("--market", type=str, default="a_stock",
                        help="市场类型: a_stock / us_stock / crypto / fund")
    parser.add_argument("--period", type=str, default="max",
                        help="数据周期: 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, 20y, 50y, max")
    parser.add_argument("--no-ai", action="store_true",
                        help="禁用 AI 分析（仅使用技术指标）")
    parser.add_argument("--interactive", "-i", action="store_true",
                        help="进入交互模式")
    parser.add_argument("--paper-trade", "-p", action="store_true",
                        help="启用模拟盘交易模式")
    args = parser.parse_args()

    print_banner()

    # 检查配置文件
    if not Path("config.yaml").exists():
        print("错误: 找不到 config.yaml，请先配置 API 密钥等参数")
        return

    if args.market == "fund":
        print("📊 基金分析模式（场外基金，数据来自东方财富）")

    agent = QuantAgent(config_path="config.yaml", paper_trade=args.paper_trade)
    visualizer = ReportVisualizer()

    # 交互模式（没有指定--symbol时默认进入交互模式）
    if args.interactive or not args.symbol:
        interactive_mode(agent)
        return

    # 单次分析模式
    result = agent.analyze(
        symbol=args.symbol,
        market=args.market,
        period=args.period,
        use_ai=not args.no_ai,
    )

    # 生成可视化报告
    print("\n🎨 正在生成可视化报告...")
    visualizer.plot_analysis(result["df"], result["symbol"], save=True)
    if result.get("backtest"):
        visualizer.plot_equity_curve(
            result["backtest"].equity_curve,
            title=f"{result['symbol']} 策略收益曲线",
            save=True,
        )

    print("\n✅ 分析完成！")


if __name__ == "__main__":
    main()
