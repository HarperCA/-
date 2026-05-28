"""
可视化报告模块
生成K线图、指标图、收益曲线图
"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
import os

from core.console import configure_console_output

configure_console_output()

# 设置中文字体
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False


class ReportVisualizer:
    """量化报告可视化器"""

    def __init__(self, output_dir: str = "./reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def plot_analysis(
        self,
        df: pd.DataFrame,
        symbol: str,
        backtest_equity: pd.Series = None,
        save: bool = True,
        show: bool = False,
    ) -> str:
        """
        绘制综合分析图（K线+均线+MACD+RSI）
        返回保存的文件路径
        """
        fig, axes = plt.subplots(
            3, 1, figsize=(14, 10),
            gridspec_kw={"height_ratios": [3, 1, 1]},
            sharex=True,
        )
        fig.suptitle(f"{symbol} 技术分析图表", fontsize=16, fontweight="bold")

        # --- 主图: K线 + 均线 + 布林带 ---
        ax1 = axes[0]
        ax1.plot(df.index, df["close"], label="收盘价", linewidth=1.5, color="black")

        colors = {"MA5": "orange", "MA10": "blue", "MA20": "purple",
                  "MA30": "green", "MA60": "red"}
        for ma, color in colors.items():
            if ma in df.columns:
                ax1.plot(df.index, df[ma], label=ma, color=color, alpha=0.7, linewidth=1)

        if "BB_Upper" in df.columns:
            ax1.fill_between(df.index, df["BB_Upper"], df["BB_Lower"],
                             alpha=0.1, color="blue", label="布林带")
            ax1.plot(df.index, df["BB_Upper"], "--", color="blue", alpha=0.5, linewidth=0.8)
            ax1.plot(df.index, df["BB_Lower"], "--", color="blue", alpha=0.5, linewidth=0.8)

        ax1.set_ylabel("价格")
        ax1.legend(loc="upper left", fontsize=8)
        ax1.grid(True, alpha=0.3)

        # --- 副图1: MACD ---
        ax2 = axes[1]
        if "MACD" in df.columns:
            ax2.plot(df.index, df["MACD"], label="MACD", color="blue", linewidth=1)
            ax2.plot(df.index, df["MACD_Signal"], label="信号线", color="red", linewidth=1)
            colors_hist = ["green" if h >= 0 else "red" for h in df["MACD_Hist"].fillna(0)]
            ax2.bar(df.index, df["MACD_Hist"].fillna(0), color=colors_hist, alpha=0.6, width=1)
            ax2.axhline(0, color="black", linewidth=0.5)
            ax2.set_ylabel("MACD")
            ax2.legend(loc="upper left", fontsize=8)
            ax2.grid(True, alpha=0.3)

        # --- 副图2: RSI ---
        ax3 = axes[2]
        if "RSI" in df.columns:
            ax3.plot(df.index, df["RSI"], label="RSI", color="purple", linewidth=1.2)
            ax3.axhline(70, color="red", linestyle="--", linewidth=1, label="超买(70)")
            ax3.axhline(30, color="green", linestyle="--", linewidth=1, label="超卖(30)")
            ax3.fill_between(df.index, 30, 70, alpha=0.1, color="gray")
            ax3.set_ylabel("RSI")
            ax3.set_ylim(0, 100)
            ax3.legend(loc="upper left", fontsize=8)
            ax3.grid(True, alpha=0.3)

        # 格式化x轴日期
        for ax in axes:
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.xticks(rotation=45)
        plt.tight_layout()

        filepath = None
        if save:
            filepath = self.output_dir / f"{symbol.replace('-', '_')}_analysis.png"
            plt.savefig(filepath, dpi=150, bbox_inches="tight")
            print(f"📁 图表已保存: {filepath}")

        if show:
            plt.show()
        else:
            plt.close(fig)

        return str(filepath) if filepath else ""

    def plot_equity_curve(
        self,
        equity_curve: pd.Series,
        benchmark_curve: pd.Series = None,
        title: str = "策略收益曲线",
        save: bool = True,
        show: bool = False,
    ) -> str:
        """绘制权益曲线对比图"""
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(equity_curve.index, equity_curve, label="策略", linewidth=2, color="blue")

        if benchmark_curve is not None:
            ax.plot(benchmark_curve.index, benchmark_curve, label="买入持有",
                    linewidth=1.5, color="gray", linestyle="--")

        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xlabel("日期")
        ax.set_ylabel("资金")
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()

        filepath = None
        if save:
            filepath = self.output_dir / "equity_curve.png"
            plt.savefig(filepath, dpi=150, bbox_inches="tight")
            print(f"📁 收益曲线已保存: {filepath}")

        if show:
            plt.show()
        else:
            plt.close(fig)

        return str(filepath) if filepath else ""
