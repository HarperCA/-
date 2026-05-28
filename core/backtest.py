"""
回测引擎模块
支持向量化回测，输出收益率曲线、最大回撤、夏普比率等
"""
import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class BacktestResult:
    """回测结果容器"""
    total_return: float              # 总收益率
    annual_return: float             # 年化收益率
    cagr: float                      # 平均复合增长率（CAGR）
    avg_rolling_1y_return: float     # 滚动平均一年回报率
    avg_monthly_return: float        # 平均月度回报率
    regressed_annual_return: float   # 回归年度回报率（对数线性回归年化）
    max_drawdown: float              # 最大回撤
    max_drawdown_duration: int       # 最长衰落期（交易日）
    volatility: float                # 年化波动率（回报标准差）
    r_squared: float                 # R²（与买入持有的相关度）
    sharpe_ratio: float              # 夏普比率
    win_rate: float                  # 胜率
    trade_count: int                 # 交易次数
    avg_win: float                   # 平均盈利
    avg_loss: float                  # 平均亏损
    expected_value: float            # 单次交易期望值
    profit_loss_ratio: float         # 盈亏比
    equity_curve: pd.Series          # 权益曲线
    trades: List[Dict]               # 交易记录
    monte_carlo: dict                # 蒙特卡洛模拟结果
    summary: str                     # 文字摘要


class BacktestEngine:
    """简单的向量化回测引擎"""

    def __init__(self, initial_cash: float = 100000.0,
                 commission: float = 0.0003, slippage: float = 0.001,
                 fund_mode: bool = False,
                 subscribe_fee: float = 0.001,      # 基金申购费率
                 redeem_fee_tiers: dict = None):     # 赎回费率阶梯
        self.initial_cash = initial_cash
        self.commission = commission
        self.slippage = slippage
        self.fund_mode = fund_mode
        self.subscribe_fee = subscribe_fee
        # 默认赎回费率: <7天 1.5%, 7-30天 0.75%, 30-365天 0.5%, >365天 0%
        self.redeem_fee_tiers = redeem_fee_tiers or {
            7: 0.015,
            30: 0.0075,
            365: 0.005,
            999999: 0.0,
        }

    def run(
        self,
        df: pd.DataFrame,
        signal_col: str = "signal",  # 信号列: 1买入, -1卖出, 0持仓不变
    ) -> BacktestResult:
        """
        执行回测
        signal_col: DataFrame中包含交易信号的列名
            1  = 满仓买入/持有
            0  = 空仓
            -1 = 做空（暂不实现，仅平多）
        """
        df = df.copy()
        # 确保信号列存在，默认持有多仓
        if signal_col not in df.columns:
            df[signal_col] = 1

        # 价格序列
        price = df["close"]
        returns = price.pct_change().fillna(0)
        signal = df[signal_col].fillna(0)

        # 持仓状态
        # 如果信号包含-1，说明是 1/0/-1 格式（0=维持现状），需要ffill
        # 如果只有0/1，说明0=空仓，直接clip即可
        if (signal == -1).any():
            position = signal.replace(0, pd.NA).ffill().fillna(0)
        else:
            position = signal
        position = position.clip(0, 1)  # 只做多，仓位0或1

        # 策略每日收益 = 持仓 * 标的收益
        strategy_returns = position.shift(1) * returns  # 用昨日信号决定今日持仓

        # 计算交易成本
        trades = position.diff().abs()  # 持仓变化（用于统计交易次数）
        if self.fund_mode:
            # 基金模式：申购费 + 赎回费（按持有期限）
            cost = self._calc_fund_costs(df, signal)
        else:
            cost = trades * (self.commission + self.slippage)
        strategy_returns = strategy_returns - cost

        # 权益曲线
        equity_curve = (1 + strategy_returns).cumprod() * self.initial_cash
        equity_curve.iloc[0] = self.initial_cash

        # 计算统计指标
        total_return = equity_curve.iloc[-1] / self.initial_cash - 1
        days = len(df)
        years = days / 252
        annual_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
        cagr = annual_return  # CAGR = 年化复利收益率

        # 滚动平均一年回报率
        if len(equity_curve) > 252:
            rolling_1y = equity_curve.pct_change(252).dropna()
            avg_rolling_1y_return = rolling_1y.mean() if len(rolling_1y) > 0 else total_return
        else:
            avg_rolling_1y_return = total_return

        # 平均月度回报率（基于日收益）
        avg_monthly_return = strategy_returns.mean() * 21  # 21个交易日≈1个月

        # 回归年度回报率（对数净值线性回归）
        log_nav = np.log(equity_curve)
        x = np.arange(len(log_nav), dtype=float)
        y = log_nav.values.astype(float)
        n = len(x)
        sum_x = np.sum(x)
        sum_y = np.sum(y)
        sum_xy = np.sum(x * y)
        sum_x2 = np.sum(x * x)
        denominator = n * sum_x2 - sum_x * sum_x
        if denominator != 0:
            slope = (n * sum_xy - sum_x * sum_y) / denominator
            regressed_annual_return = np.exp(slope * 252) - 1
        else:
            regressed_annual_return = 0.0

        # 最大回撤
        cummax = equity_curve.cummax()
        drawdown = (equity_curve - cummax) / cummax
        max_drawdown = drawdown.min()

        # 夏普比率（假设无风险利率为0）
        daily_return = strategy_returns
        sharpe_ratio = daily_return.mean() / daily_return.std() * np.sqrt(252) if daily_return.std() != 0 else 0

        # 年化波动率
        volatility = daily_return.std() * np.sqrt(252)

        # 最长衰落期（交易日）：从peak到recovery的最长天数
        cummax = equity_curve.cummax()
        batch = (cummax != cummax.shift(1)).cumsum()
        max_drawdown_duration = int(batch.groupby(batch).size().max()) if len(batch) > 0 else 0

        # R²：策略收益与买入持有的相关度
        benchmark_returns = returns
        common_mask = strategy_returns.notna() & benchmark_returns.notna()
        s_ret = strategy_returns[common_mask]
        b_ret = benchmark_returns[common_mask]
        if len(s_ret) > 2 and s_ret.std() > 0 and b_ret.std() > 0:
            correlation = np.corrcoef(s_ret, b_ret)[0, 1]
            r_squared = correlation ** 2
        else:
            r_squared = 0.0

        # 交易次数与胜率
        trade_signals = trades[trades > 0]
        trade_count = len(trade_signals)

        # 简单估算胜率：每次换仓后下一日收益为正的比例
        trade_entries = position.diff()[position.diff() > 0].index
        wins = 0
        for t in trade_entries:
            try:
                idx = df.index.get_loc(t)
                if idx + 1 < len(df):
                    if df["close"].iloc[idx + 1] > df["close"].iloc[idx]:
                        wins += 1
            except Exception:
                pass
        win_rate = wins / len(trade_entries) if len(trade_entries) > 0 else 0

        # 生成交易记录（简化版）
        trades_list = []
        in_position = False
        entry_price = 0
        entry_date = None
        for date, row in df.iterrows():
            sig = row.get(signal_col, 0)
            if sig == 1 and not in_position:
                in_position = True
                entry_price = row["close"]
                entry_date = date
            elif sig == 0 and in_position:
                in_position = False
                pnl = row["close"] / entry_price - 1
                trades_list.append({
                    "买入日期": entry_date,
                    "卖出日期": date,
                    "买入价": round(entry_price, 2),
                    "卖出价": round(row["close"], 2),
                    "收益率": f"{pnl*100:.2f}%",
                })

        # 计算平均盈利/亏损、盈亏比、期望值
        trade_pnls = []
        for t in trades_list:
            pnl_str = t["收益率"].replace("%", "")
            try:
                trade_pnls.append(float(pnl_str) / 100)
            except ValueError:
                pass

        avg_win = np.mean([p for p in trade_pnls if p > 0]) if any(p > 0 for p in trade_pnls) else 0
        avg_loss = abs(np.mean([p for p in trade_pnls if p < 0])) if any(p < 0 for p in trade_pnls) else 0
        profit_loss_ratio = avg_win / avg_loss if avg_loss != 0 else float('inf')
        expected_value = win_rate * avg_win - (1 - win_rate) * avg_loss

        # 蒙特卡洛模拟 (Bootstrap)
        mc = self.monte_carlo(equity_curve)
        mc_report = ""
        if mc:
            mc_report = (
                f"\n🎲 蒙特卡洛模拟 (Bootstrap {mc['n_simulations']:,}次, {mc['n_days']}天):\n"
                f"📈 收益分布:\n"
                f"  胜率: {mc['win_rate']*100:.1f}%\n"
                f"  平均收益: {mc['mean_return']*100:.2f}%\n"
                f"  中位数收益: {mc['median_return']*100:.2f}%\n"
                f"  最好5%: {mc['p95_return']*100:.2f}%\n"
                f"  最差5%: {mc['p5_return']*100:.2f}%\n"
                f"  25分位: {mc['p25_return']*100:.2f}%\n"
                f"  75分位: {mc['p75_return']*100:.2f}%\n"
                f"⚠️ 回撤分布:\n"
                f"  平均最大回撤: {mc['mean_max_dd']*100:.2f}%\n"
                f"  最差5%回撤: {mc['p5_max_dd']*100:.2f}%\n"
                f"  回撤超20%概率: {mc['prob_20pct_dd']*100:.1f}%\n"
                f"  回撤超30%概率: {mc['prob_30pct_dd']*100:.1f}%\n"
            )

        summary = (
            f"回测统计:\n"
            f"\n📈 收益指标:\n"
            f"  总收益率: {total_return*100:.2f}%\n"
            f"  年化收益(CAGR): {cagr*100:.2f}%\n"
            f"  滚动平均一年回报: {avg_rolling_1y_return*100:.2f}%\n"
            f"  平均月度回报: {avg_monthly_return*100:.2f}%\n"
            f"  回归年度回报: {regressed_annual_return*100:.2f}%\n"
            f"\n⚠️ 风险指标:\n"
            f"  最大回撤: {max_drawdown*100:.2f}%\n"
            f"  最长衰落期: {max_drawdown_duration} 个交易日\n"
            f"  年化波动率: {volatility*100:.2f}%\n"
            f"  R²(与基准相关度): {r_squared:.2f}\n"
            f"\n🎯 交易质量:\n"
            f"  夏普比率: {sharpe_ratio:.2f}\n"
            f"  交易次数: {trade_count}\n"
            f"  胜率: {win_rate*100:.1f}%\n"
            f"  平均盈利: {avg_win*100:.2f}%\n"
            f"  平均亏损: {avg_loss*100:.2f}%\n"
            f"  盈亏比: {profit_loss_ratio:.2f}\n"
            f"  单次期望值: {expected_value*100:.2f}%\n"
            f"{mc_report}"
        )

        return BacktestResult(
            total_return=total_return,
            annual_return=annual_return,
            cagr=cagr,
            avg_rolling_1y_return=avg_rolling_1y_return,
            avg_monthly_return=avg_monthly_return,
            regressed_annual_return=regressed_annual_return,
            max_drawdown=max_drawdown,
            max_drawdown_duration=max_drawdown_duration,
            volatility=volatility,
            r_squared=r_squared,
            sharpe_ratio=sharpe_ratio,
            win_rate=win_rate,
            trade_count=trade_count,
            avg_win=avg_win,
            avg_loss=avg_loss,
            expected_value=expected_value,
            profit_loss_ratio=profit_loss_ratio,
            equity_curve=equity_curve,
            trades=trades_list,
            monte_carlo=mc,
            summary=summary,
        )

    def _calc_fund_costs(self, df: pd.DataFrame, signal: pd.Series) -> pd.Series:
        """计算基金申赎成本（向量化）"""
        cost = pd.Series(0.0, index=df.index)
        entry_dates = {}  # 记录每次买入的日期

        for i, (date, sig) in enumerate(signal.items()):
            if sig == 1 and (i == 0 or signal.iloc[i-1] == 0):
                # 申购：扣申购费
                cost.iloc[i] = self.subscribe_fee
                entry_dates[date] = date
            elif sig == 0 and i > 0 and signal.iloc[i-1] == 1:
                # 赎回：找最后一次买入日期，计算持有天数
                if entry_dates:
                    last_entry = max(entry_dates.values())
                    hold_days = (date - last_entry).days
                    # 查找适用费率
                    redeem_rate = 0.0
                    for threshold, rate in sorted(self.redeem_fee_tiers.items()):
                        if hold_days < threshold:
                            redeem_rate = rate
                            break
                    cost.iloc[i] = redeem_rate
                    entry_dates.clear()
        return cost

    def monte_carlo(self, equity_curve: pd.Series, n_simulations: int = 10000, n_days: int = 252) -> dict:
        """
        Bootstrap蒙特卡洛模拟
        从历史日收益中有放回抽样，模拟未来n_days天的走势
        """
        returns = equity_curve.pct_change().dropna().values
        if len(returns) < 10:
            return {}

        np.random.seed(42)
        sampled = np.random.choice(returns, size=(n_simulations, n_days), replace=True)

        initial = equity_curve.iloc[-1]
        curves = initial * np.cumprod(1 + sampled, axis=1)

        final_values = curves[:, -1]
        total_returns = final_values / initial - 1

        running_max = np.maximum.accumulate(curves, axis=1)
        drawdowns = (curves - running_max) / running_max
        max_drawdowns = np.min(drawdowns, axis=1)

        return {
            "n_simulations": n_simulations,
            "n_days": n_days,
            "win_rate": float(np.mean(total_returns > 0)),
            "mean_return": float(np.mean(total_returns)),
            "median_return": float(np.median(total_returns)),
            "p5_return": float(np.percentile(total_returns, 5)),
            "p25_return": float(np.percentile(total_returns, 25)),
            "p75_return": float(np.percentile(total_returns, 75)),
            "p95_return": float(np.percentile(total_returns, 95)),
            "mean_max_dd": float(np.mean(max_drawdowns)),
            "p5_max_dd": float(np.percentile(max_drawdowns, 5)),
            "p95_max_dd": float(np.percentile(max_drawdowns, 95)),
            "prob_20pct_dd": float(np.mean(max_drawdowns <= -0.20)),
            "prob_30pct_dd": float(np.mean(max_drawdowns <= -0.30)),
        }

    def benchmark_buy_and_hold(self, df: pd.DataFrame) -> BacktestResult:
        """买入持有作为基准对比"""
        df = df.copy()
        df["signal"] = 1  # 永远满仓
        return self.run(df, signal_col="signal")
