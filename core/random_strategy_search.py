"""Random strategy search over the existing long/cash backtest engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import random
from pathlib import Path
from typing import Callable, Iterable

import numpy as np
import pandas as pd

from core.backtest import BacktestEngine
from core.indicators import add_all_indicators


@dataclass(frozen=True)
class Condition:
    feature: str
    op: str
    value: float | None = None


@dataclass(frozen=True)
class RandomStrategySpec:
    key: str
    entry: tuple[Condition, ...]
    exit: tuple[Condition, ...]
    min_hold_days: int
    cooldown_days: int


@dataclass
class StrategyScore:
    key: str
    score: float
    avg_cagr: float
    avg_total_return: float
    avg_max_drawdown: float
    avg_sharpe: float
    total_trades: int
    positive_assets: int
    asset_results: list[dict]
    spec: RandomStrategySpec


FEATURE_BUILDERS: dict[str, Callable[[pd.DataFrame], pd.Series]] = {
    "rsi": lambda df: df["RSI"],
    "macd_hist": lambda df: df["MACD_Hist"],
    "mom_10": lambda df: df["close"].pct_change(10),
    "mom_20": lambda df: df["close"].pct_change(20),
    "mom_60": lambda df: df["close"].pct_change(60),
    "close_vs_ma10": lambda df: df["close"] / df["MA10"] - 1,
    "close_vs_ma20": lambda df: df["close"] / df["MA20"] - 1,
    "close_vs_ma60": lambda df: df["close"] / df["MA60"] - 1,
    "ma10_vs_ma30": lambda df: df["MA10"] / df["MA30"] - 1,
    "ma20_vs_ma60": lambda df: df["MA20"] / df["MA60"] - 1,
    "vol_20": lambda df: df["close"].pct_change().rolling(20, min_periods=20).std() * np.sqrt(252),
    "drawdown_60": lambda df: df["close"] / df["close"].rolling(60, min_periods=30).max() - 1,
    "breakout_20": lambda df: df["close"] / df["close"].rolling(20, min_periods=20).max() - 1,
    "breakout_60": lambda df: df["close"] / df["close"].rolling(60, min_periods=30).max() - 1,
}


THRESHOLDS: dict[str, tuple[float, float]] = {
    "rsi": (25.0, 75.0),
    "macd_hist": (-0.04, 0.04),
    "mom_10": (-0.06, 0.08),
    "mom_20": (-0.10, 0.14),
    "mom_60": (-0.20, 0.30),
    "close_vs_ma10": (-0.08, 0.08),
    "close_vs_ma20": (-0.12, 0.12),
    "close_vs_ma60": (-0.20, 0.20),
    "ma10_vs_ma30": (-0.08, 0.08),
    "ma20_vs_ma60": (-0.12, 0.12),
    "vol_20": (0.08, 0.70),
    "drawdown_60": (-0.30, -0.02),
    "breakout_20": (-0.12, 0.0),
    "breakout_60": (-0.25, 0.0),
}


def prepare_market_data(df: pd.DataFrame) -> pd.DataFrame:
    """Add indicators and derived random-search features once per dataset."""
    data = add_all_indicators(df.copy())
    for name, builder in FEATURE_BUILDERS.items():
        data[f"RS_{name}"] = builder(data).replace([np.inf, -np.inf], np.nan)
    return data


def load_default_datasets(data_dir: str | Path = "data/cleaned") -> list[dict]:
    """Load all available max-history datasets, falling back to 1y data."""
    root = Path(data_dir)
    paths = sorted(root.glob("*_max_1d.csv"))
    if not paths:
        paths = sorted(root.glob("*_1y_1d.csv"))

    datasets = []
    for path in paths:
        df = pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()
        if len(df) < 120:
            continue
        label = path.stem.replace("_max_1d", "").replace("_1y_1d", "")
        datasets.append(
            {
                "label": label,
                "path": str(path),
                "fund_mode": label.startswith("fund_"),
                "data": prepare_market_data(df),
            }
        )
    return datasets


def random_condition(rng: random.Random) -> Condition:
    feature = rng.choice(tuple(THRESHOLDS))
    low, high = THRESHOLDS[feature]
    value = rng.uniform(low, high)
    op = rng.choice((">", "<"))
    return Condition(feature=feature, op=op, value=round(value, 6))


def generate_random_strategy(rng: random.Random, generation: int, slot: int) -> RandomStrategySpec:
    entry_count = rng.randint(2, 4)
    exit_count = rng.randint(1, 3)
    entry = tuple(random_condition(rng) for _ in range(entry_count))
    exit_ = tuple(random_condition(rng) for _ in range(exit_count))
    return RandomStrategySpec(
        key=f"g{generation:03d}_{slot:02d}_{rng.randrange(1_000_000):06d}",
        entry=entry,
        exit=exit_,
        min_hold_days=rng.choice((1, 3, 5, 10, 15, 20, 30)),
        cooldown_days=rng.choice((0, 2, 5, 10, 15)),
    )


def condition_mask(df: pd.DataFrame, condition: Condition) -> pd.Series:
    series = df[f"RS_{condition.feature}"]
    if condition.op == ">":
        return series > float(condition.value)
    if condition.op == "<":
        return series < float(condition.value)
    raise ValueError(f"Unsupported operator: {condition.op}")


def apply_holding_rules(raw: pd.Series, min_hold_days: int, cooldown_days: int) -> pd.Series:
    target = raw.fillna(0).astype(int).clip(0, 1)
    position = []
    current = 0
    hold_days = 0
    cooldown = 0

    for desired in target:
        if current:
            hold_days += 1
            if desired == 0 and hold_days >= min_hold_days:
                current = 0
                hold_days = 0
                cooldown = cooldown_days
        else:
            if cooldown > 0:
                cooldown -= 1
            elif desired == 1:
                current = 1
                hold_days = 1
        position.append(current)
    return pd.Series(position, index=raw.index, dtype=int)


def build_signal(df: pd.DataFrame, spec: RandomStrategySpec) -> pd.Series:
    entry = pd.Series(True, index=df.index)
    for condition in spec.entry:
        entry &= condition_mask(df, condition).fillna(False)

    exit_ = pd.Series(False, index=df.index)
    for condition in spec.exit:
        exit_ |= condition_mask(df, condition).fillna(False)

    raw = pd.Series(pd.NA, index=df.index, dtype="object")
    raw[entry] = 1
    raw[exit_] = 0
    position = raw.ffill().fillna(0).astype(int)
    return apply_holding_rules(position, spec.min_hold_days, spec.cooldown_days)


def _score_metrics(results: list[dict]) -> float:
    cagr_terms = [np.tanh(row["cagr"]) for row in results]
    sharpe_terms = [np.tanh(row["sharpe_ratio"] / 2.0) for row in results]
    drawdown_terms = [max(0.0, 1.0 + row["max_drawdown"]) for row in results]
    severe_drawdowns = [max(0.0, abs(row["max_drawdown"]) - 0.50) for row in results]
    positive_assets = sum(1 for row in results if row["total_return"] > 0)
    trade_years = sum(row["years"] for row in results)
    trades_per_year = sum(row["trade_count"] for row in results) / max(trade_years, 1.0)
    turnover_penalty = max(0.0, trades_per_year - 6.0) * 0.01
    inactivity_penalty = 0.08 if sum(row["trade_count"] for row in results) == 0 else 0.0
    consistency = positive_assets / max(len(results), 1)
    return float(
        0.35 * np.mean(cagr_terms)
        + 0.25 * np.mean(sharpe_terms)
        + 0.30 * np.mean(drawdown_terms)
        + 0.10 * consistency
        - 1.20 * np.mean(severe_drawdowns)
        - turnover_penalty
        - inactivity_penalty
    )


def evaluate_strategy(
    spec: RandomStrategySpec,
    datasets: Iterable[dict],
    initial_cash: float = 100000,
) -> StrategyScore:
    asset_results = []
    for dataset in datasets:
        data = dataset["data"].copy()
        data["strategy_signal"] = build_signal(data, spec)
        result = BacktestEngine(initial_cash=initial_cash, fund_mode=dataset["fund_mode"]).run(
            data,
            signal_col="strategy_signal",
        )
        years = len(data) / 252
        asset_results.append(
            {
                "label": dataset["label"],
                "total_return": float(result.total_return),
                "cagr": float(result.cagr),
                "max_drawdown": float(result.max_drawdown),
                "sharpe_ratio": float(result.sharpe_ratio),
                "trade_count": int(result.trade_count),
                "final_value": float(result.equity_curve.iloc[-1]),
                "years": float(years),
            }
        )

    return StrategyScore(
        key=spec.key,
        score=float(_score_metrics(asset_results)),
        avg_cagr=float(np.mean([row["cagr"] for row in asset_results])),
        avg_total_return=float(np.mean([row["total_return"] for row in asset_results])),
        avg_max_drawdown=float(np.mean([row["max_drawdown"] for row in asset_results])),
        avg_sharpe=float(np.mean([row["sharpe_ratio"] for row in asset_results])),
        total_trades=sum(row["trade_count"] for row in asset_results),
        positive_assets=sum(1 for row in asset_results if row["total_return"] > 0),
        asset_results=asset_results,
        spec=spec,
    )


def run_random_strategy_search(
    datasets: list[dict],
    rounds: int = 20,
    seed: int = 42,
    initial_cash: float = 100000,
) -> dict:
    """Run champion-plus-nine random strategy search."""
    if rounds < 1:
        raise ValueError("rounds must be at least 1")
    if not datasets:
        raise ValueError("at least one dataset is required")

    rng = random.Random(seed)
    champion: StrategyScore | None = None
    history = []

    for generation in range(1, rounds + 1):
        random_count = 10 if champion is None else 9
        specs = [generate_random_strategy(rng, generation, slot) for slot in range(random_count)]
        if champion is not None:
            specs.append(champion.spec)

        scores = [evaluate_strategy(spec, datasets, initial_cash=initial_cash) for spec in specs]
        scores.sort(key=lambda item: item.score, reverse=True)
        champion = scores[0]
        history.append(
            {
                "round": generation,
                "champion_key": champion.key,
                "champion_score": champion.score,
                "champion_avg_cagr": champion.avg_cagr,
                "champion_avg_max_drawdown": champion.avg_max_drawdown,
                "champion_avg_sharpe": champion.avg_sharpe,
                "winner_was_carried": champion.key == history[-1]["champion_key"] if history else False,
                "candidates": [score_to_dict(score, include_spec=False) for score in scores],
            }
        )

    assert champion is not None
    return {
        "seed": seed,
        "rounds": rounds,
        "dataset_count": len(datasets),
        "datasets": [
            {
                "label": dataset["label"],
                "path": dataset["path"],
                "rows": len(dataset["data"]),
                "fund_mode": dataset["fund_mode"],
            }
            for dataset in datasets
        ],
        "champion": score_to_dict(champion, include_spec=True),
        "history": history,
    }


def spec_to_dict(spec: RandomStrategySpec) -> dict:
    data = asdict(spec)
    data["entry"] = [asdict(condition) for condition in spec.entry]
    data["exit"] = [asdict(condition) for condition in spec.exit]
    return data


def score_to_dict(score: StrategyScore, include_spec: bool = True) -> dict:
    data = {
        "key": score.key,
        "score": score.score,
        "avg_cagr": score.avg_cagr,
        "avg_total_return": score.avg_total_return,
        "avg_max_drawdown": score.avg_max_drawdown,
        "avg_sharpe": score.avg_sharpe,
        "total_trades": score.total_trades,
        "positive_assets": score.positive_assets,
        "asset_results": score.asset_results,
    }
    if include_spec:
        data["spec"] = spec_to_dict(score.spec)
    return data


def save_search_report(report: dict, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
