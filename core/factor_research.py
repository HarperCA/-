"""Factor research helpers for cross-sectional quant analysis."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

from core.indicators import add_volatility_adjusted_momentum


@dataclass(frozen=True)
class VmomParams:
    momentum_window: int = 63
    volatility_window: int = 20
    zscore_window: int = 120


def _spearman_corr(left: pd.Series, right: pd.Series) -> float:
    return float(left.rank(method="average").corr(right.rank(method="average")))


def read_ohlcv_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    df = df.dropna(subset=["date"]).set_index("date").sort_index()
    return df[["open", "high", "low", "close", "volume"]]


def build_vmom_panel(
    series_by_asset: dict[str, pd.DataFrame],
    params: VmomParams = VmomParams(),
    forward_days: Iterable[int] = (1, 5, 20),
) -> pd.DataFrame:
    frames = []
    for asset, df in series_by_asset.items():
        data = add_volatility_adjusted_momentum(
            df.copy(),
            momentum_window=params.momentum_window,
            volatility_window=params.volatility_window,
            zscore_window=params.zscore_window,
        )
        data["asset"] = asset
        for horizon in forward_days:
            data[f"forward_return_{horizon}d"] = data["close"].shift(-horizon) / data["close"] - 1
        frames.append(data.reset_index().rename(columns={"index": "date"}))

    if not frames:
        return pd.DataFrame()
    panel = pd.concat(frames, ignore_index=True)
    panel = panel.rename(columns={panel.columns[0]: "date"} if panel.columns[0] != "date" else {})
    return panel.sort_values(["date", "asset"]).reset_index(drop=True)


def cross_sectional_ic(
    panel: pd.DataFrame,
    factor_col: str = "Factor_VMOM",
    forward_col: str = "forward_return_5d",
    min_assets: int = 3,
) -> pd.DataFrame:
    rows = []
    for date, group in panel.dropna(subset=[factor_col, forward_col]).groupby("date"):
        if len(group) < min_assets:
            continue
        if group[factor_col].nunique() < 2 or group[forward_col].nunique() < 2:
            continue
        rows.append(
            {
                "date": date,
                "pearson_ic": group[factor_col].corr(group[forward_col], method="pearson"),
                "spearman_ic": _spearman_corr(group[factor_col], group[forward_col]),
                "asset_count": len(group),
            }
        )
    return pd.DataFrame(rows)


def quantile_forward_returns(
    panel: pd.DataFrame,
    factor_col: str = "Factor_VMOM",
    forward_col: str = "forward_return_5d",
    quantiles: int = 3,
    min_assets: int = 3,
) -> pd.DataFrame:
    rows = []
    for date, group in panel.dropna(subset=[factor_col, forward_col]).groupby("date"):
        if len(group) < min_assets or group[factor_col].nunique() < 2:
            continue
        bucket_count = min(quantiles, len(group))
        ranked = group[factor_col].rank(method="first")
        buckets = pd.qcut(ranked, q=bucket_count, labels=False, duplicates="drop") + 1
        enriched = group.assign(quantile=buckets.astype(int))
        for quantile, bucket in enriched.groupby("quantile"):
            rows.append(
                {
                    "date": date,
                    "quantile": int(quantile),
                    "mean_forward_return": float(bucket[forward_col].mean()),
                    "asset_count": int(len(bucket)),
                }
            )
    return pd.DataFrame(rows)


def summarize_factor_run(
    panel: pd.DataFrame,
    params: VmomParams,
    horizon: int = 5,
    quantiles: int = 3,
    min_assets: int = 3,
) -> dict:
    forward_col = f"forward_return_{horizon}d"
    ic = cross_sectional_ic(panel, forward_col=forward_col, min_assets=min_assets)
    qret = quantile_forward_returns(panel, forward_col=forward_col, quantiles=quantiles, min_assets=min_assets)

    long_short_mean = 0.0
    top_quantile_mean = 0.0
    bottom_quantile_mean = 0.0
    if not qret.empty:
        wide = qret.pivot_table(index="date", columns="quantile", values="mean_forward_return", aggfunc="mean")
        if not wide.empty:
            bottom = wide.columns.min()
            top = wide.columns.max()
            spread = wide[top] - wide[bottom]
            long_short_mean = float(spread.mean())
            top_quantile_mean = float(wide[top].mean())
            bottom_quantile_mean = float(wide[bottom].mean())

    return {
        "momentum_window": params.momentum_window,
        "volatility_window": params.volatility_window,
        "zscore_window": params.zscore_window,
        "horizon": horizon,
        "ic_count": int(len(ic)),
        "pearson_ic_mean": float(ic["pearson_ic"].mean()) if not ic.empty else 0.0,
        "spearman_ic_mean": float(ic["spearman_ic"].mean()) if not ic.empty else 0.0,
        "top_quantile_mean": top_quantile_mean,
        "bottom_quantile_mean": bottom_quantile_mean,
        "long_short_mean": long_short_mean,
    }


def run_vmom_parameter_grid(
    series_by_asset: dict[str, pd.DataFrame],
    momentum_windows: Iterable[int] = (21, 42, 63, 84),
    volatility_windows: Iterable[int] = (10, 20, 30),
    zscore_window: int = 120,
    horizon: int = 5,
    quantiles: int = 3,
    min_assets: int = 3,
) -> pd.DataFrame:
    rows = []
    for momentum_window in momentum_windows:
        for volatility_window in volatility_windows:
            params = VmomParams(momentum_window, volatility_window, zscore_window)
            panel = build_vmom_panel(series_by_asset, params=params, forward_days=(horizon,))
            rows.append(
                summarize_factor_run(
                    panel,
                    params=params,
                    horizon=horizon,
                    quantiles=quantiles,
                    min_assets=min_assets,
                )
            )
    result = pd.DataFrame(rows)
    if result.empty:
        return result
    return result.sort_values(["spearman_ic_mean", "long_short_mean"], ascending=False).reset_index(drop=True)
