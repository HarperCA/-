"""SQLite-backed factor library for research, backtests, and production reuse."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd


DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "quant_app.sqlite"


@dataclass(frozen=True)
class FactorSpec:
    name: str
    category: str
    description: str
    frequency: str = "1d"
    source: str = "market_ohlcv"
    version: str = "v1"
    parameters: dict[str, Any] | None = None


MARKET_FACTOR_SPECS = [
    FactorSpec("return_1d", "momentum", "Daily close-to-close return."),
    FactorSpec("return_5d", "momentum", "Five day close-to-close return.", parameters={"window": 5}),
    FactorSpec("momentum_5d", "momentum", "Five trading day close return.", parameters={"window": 5}),
    FactorSpec("momentum_20d", "momentum", "Twenty trading day close return.", parameters={"window": 20}),
    FactorSpec("reversal_5d", "reversal", "Negative five day return for short-term reversal.", parameters={"window": 5}),
    FactorSpec("ma_gap_5_20", "trend", "Five day moving average divided by twenty day moving average minus one."),
    FactorSpec("volatility_20d", "volatility", "Annualized 20 day return volatility.", parameters={"window": 20}),
    FactorSpec("downside_volatility_20d", "volatility", "Annualized downside volatility over 20 days."),
    FactorSpec("max_drawdown_20d", "volatility", "Rolling 20 day maximum drawdown."),
    FactorSpec("range_pct", "volatility", "Daily high-low range divided by close."),
    FactorSpec("volume_zscore_20d", "liquidity", "Rolling 20 day volume z-score."),
    FactorSpec("volume_change_5d", "liquidity", "Five day volume percentage change.", parameters={"window": 5}),
    FactorSpec("turnover_proxy", "liquidity", "Trading amount proxy based on close times volume."),
    FactorSpec("amihud_20d", "liquidity", "Amihud illiquidity proxy over 20 days."),
    FactorSpec("vmom_20d", "momentum", "Momentum adjusted by recent volatility.", parameters={"momentum": 20, "volatility": 20}),
]

FUNDAMENTAL_FACTOR_SPECS = [
    FactorSpec("pe_ttm", "valuation", "Trailing twelve month price-to-earnings ratio.", source="fundamental"),
    FactorSpec("pb", "valuation", "Price-to-book ratio.", source="fundamental"),
    FactorSpec("ps_ttm", "valuation", "Trailing twelve month price-to-sales ratio.", source="fundamental"),
    FactorSpec("dividend_yield", "valuation", "Trailing dividend yield.", source="fundamental"),
    FactorSpec("roe_ttm", "quality", "Trailing twelve month return on equity.", source="fundamental"),
    FactorSpec("roa_ttm", "quality", "Trailing twelve month return on assets.", source="fundamental"),
    FactorSpec("gross_margin_ttm", "quality", "Trailing gross profit margin.", source="fundamental"),
    FactorSpec("debt_to_asset", "quality", "Total liabilities divided by total assets.", source="fundamental"),
    FactorSpec("revenue_growth_yoy", "growth", "Year-over-year revenue growth.", source="fundamental"),
    FactorSpec("net_profit_growth_yoy", "growth", "Year-over-year net profit growth.", source="fundamental"),
]

ALTERNATIVE_FACTOR_SPECS = [
    FactorSpec("news_sentiment", "sentiment", "Aggregated news sentiment score.", source="news"),
    FactorSpec("news_heat", "sentiment", "News mention intensity.", source="news"),
    FactorSpec("northbound_net_inflow", "flow", "Northbound net capital inflow.", source="capital_flow"),
    FactorSpec("main_fund_net_inflow", "flow", "Main fund net inflow.", source="capital_flow"),
]

ALL_FACTOR_SPECS = MARKET_FACTOR_SPECS + FUNDAMENTAL_FACTOR_SPECS + ALTERNATIVE_FACTOR_SPECS


class FactorStore:
    """Store factor metadata, versioned values, and quality snapshots in SQLite."""

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_schema()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self) -> None:
        conn = self.connect()
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS factor_definitions (
                    factor_name TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    frequency TEXT NOT NULL,
                    source TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS factor_versions (
                    factor_name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    parameters_json TEXT NOT NULL,
                    formula_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (factor_name, version),
                    FOREIGN KEY (factor_name) REFERENCES factor_definitions(factor_name)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS factor_values (
                    factor_name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    trade_date TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    market TEXT NOT NULL,
                    factor_value REAL,
                    zscore REAL,
                    rank_pct REAL,
                    industry TEXT,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (factor_name, version, trade_date, symbol, market),
                    FOREIGN KEY (factor_name, version)
                        REFERENCES factor_versions(factor_name, version)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS factor_quality (
                    factor_name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    as_of_date TEXT NOT NULL,
                    market TEXT NOT NULL,
                    row_count INTEGER NOT NULL,
                    non_null_count INTEGER NOT NULL,
                    missing_rate REAL NOT NULL,
                    mean_value REAL,
                    std_value REAL,
                    min_value REAL,
                    max_value REAL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (factor_name, version, as_of_date, market),
                    FOREIGN KEY (factor_name, version)
                        REFERENCES factor_versions(factor_name, version)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS factor_evaluations (
                    factor_name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    eval_date TEXT NOT NULL,
                    market TEXT NOT NULL,
                    horizon TEXT NOT NULL,
                    ic REAL,
                    rank_ic REAL,
                    long_short_return REAL,
                    turnover REAL,
                    coverage REAL,
                    sample_size INTEGER,
                    metrics_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (factor_name, version, eval_date, market, horizon),
                    FOREIGN KEY (factor_name, version)
                        REFERENCES factor_versions(factor_name, version)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS factor_import_batches (
                    batch_id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    market TEXT NOT NULL,
                    rows_imported INTEGER NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_factor_values_lookup
                ON factor_values (symbol, market, trade_date, factor_name)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_factor_values_date
                ON factor_values (trade_date, market, factor_name)
                """
            )
            self._migrate_schema(conn)
            conn.commit()
        finally:
            conn.close()

    def _migrate_schema(self, conn: sqlite3.Connection) -> None:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(factor_values)").fetchall()}
        for column, ddl in {
            "zscore": "ALTER TABLE factor_values ADD COLUMN zscore REAL",
            "rank_pct": "ALTER TABLE factor_values ADD COLUMN rank_pct REAL",
            "industry": "ALTER TABLE factor_values ADD COLUMN industry TEXT",
        }.items():
            if column not in columns:
                conn.execute(ddl)

    def register_factor(self, spec: FactorSpec) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        params = spec.parameters or {}
        params_json = json.dumps(params, ensure_ascii=False, sort_keys=True)
        formula_hash = hashlib.sha256(
            f"{spec.name}|{spec.category}|{spec.description}|{params_json}".encode("utf-8")
        ).hexdigest()

        conn = self.connect()
        try:
            conn.execute(
                """
                INSERT INTO factor_definitions
                    (factor_name, category, description, frequency, source, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(factor_name) DO UPDATE SET
                    category = excluded.category,
                    description = excluded.description,
                    frequency = excluded.frequency,
                    source = excluded.source,
                    updated_at = excluded.updated_at
                """,
                (spec.name, spec.category, spec.description, spec.frequency, spec.source, now, now),
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO factor_versions
                    (factor_name, version, parameters_json, formula_hash, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (spec.name, spec.version, params_json, formula_hash, now),
            )
            conn.commit()
        finally:
            conn.close()

    def upsert_values(
        self,
        factor_name: str,
        values: pd.DataFrame,
        *,
        version: str = "v1",
        market: str = "unknown",
    ) -> int:
        required = {"trade_date", "symbol", "factor_value"}
        missing = required.difference(values.columns)
        if missing:
            raise ValueError(f"factor values missing columns: {', '.join(sorted(missing))}")

        now = datetime.now().isoformat(timespec="seconds")
        frame = values[["trade_date", "symbol", "factor_value"]].copy()
        if "industry" in values.columns:
            frame["industry"] = values["industry"]
        else:
            frame["industry"] = None
        frame["trade_date"] = pd.to_datetime(frame["trade_date"], errors="coerce").dt.strftime("%Y-%m-%d")
        frame["symbol"] = frame["symbol"].astype(str)
        frame["factor_value"] = pd.to_numeric(frame["factor_value"], errors="coerce")
        frame["zscore"] = _cross_section_zscore(frame, "factor_value")
        frame["rank_pct"] = frame.groupby("trade_date")["factor_value"].rank(pct=True)
        frame = frame.dropna(subset=["trade_date", "symbol"])

        rows = [
            (
                factor_name,
                version,
                row.trade_date,
                row.symbol,
                market,
                None if pd.isna(row.factor_value) else float(row.factor_value),
                None if pd.isna(row.zscore) else float(row.zscore),
                None if pd.isna(row.rank_pct) else float(row.rank_pct),
                None if pd.isna(row.industry) else str(row.industry),
                now,
            )
            for row in frame.itertuples(index=False)
        ]
        if not rows:
            return 0

        conn = self.connect()
        try:
            conn.executemany(
                """
                INSERT INTO factor_values
                    (factor_name, version, trade_date, symbol, market, factor_value,
                     zscore, rank_pct, industry, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(factor_name, version, trade_date, symbol, market) DO UPDATE SET
                    factor_value = excluded.factor_value,
                    zscore = excluded.zscore,
                    rank_pct = excluded.rank_pct,
                    industry = excluded.industry,
                    updated_at = excluded.updated_at
                """,
                rows,
            )
            conn.commit()
        finally:
            conn.close()

        return len(rows)

    def record_quality(
        self,
        factor_name: str,
        values: pd.DataFrame,
        *,
        version: str = "v1",
        market: str = "unknown",
    ) -> None:
        if values.empty:
            return
        now = datetime.now().isoformat(timespec="seconds")
        series = pd.to_numeric(values["factor_value"], errors="coerce")
        trade_dates = pd.to_datetime(values["trade_date"], errors="coerce")
        as_of_date = trade_dates.max().strftime("%Y-%m-%d")
        row_count = int(len(series))
        non_null_count = int(series.notna().sum())
        missing_rate = 1 - (non_null_count / row_count if row_count else 0)

        stats = series.replace([np.inf, -np.inf], np.nan).dropna()
        payload = (
            factor_name,
            version,
            as_of_date,
            market,
            row_count,
            non_null_count,
            float(missing_rate),
            _nullable_float(stats.mean()),
            _nullable_float(stats.std(ddof=0)),
            _nullable_float(stats.min()),
            _nullable_float(stats.max()),
            now,
        )

        conn = self.connect()
        try:
            conn.execute(
                """
                INSERT INTO factor_quality
                    (factor_name, version, as_of_date, market, row_count, non_null_count,
                     missing_rate, mean_value, std_value, min_value, max_value, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(factor_name, version, as_of_date, market) DO UPDATE SET
                    row_count = excluded.row_count,
                    non_null_count = excluded.non_null_count,
                    missing_rate = excluded.missing_rate,
                    mean_value = excluded.mean_value,
                    std_value = excluded.std_value,
                    min_value = excluded.min_value,
                    max_value = excluded.max_value,
                    updated_at = excluded.updated_at
                """,
                payload,
            )
            conn.commit()
        finally:
            conn.close()

    def get_factor_values(
        self,
        factor_names: Iterable[str] | None = None,
        *,
        symbols: Iterable[str] | None = None,
        market: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        version: str = "v1",
        pivot: bool = False,
    ) -> pd.DataFrame:
        where = ["version = ?"]
        params: list[Any] = [version]

        _add_in_filter(where, params, "factor_name", factor_names)
        _add_in_filter(where, params, "symbol", symbols)
        if market:
            where.append("market = ?")
            params.append(market)
        if start_date:
            where.append("trade_date >= ?")
            params.append(start_date)
        if end_date:
            where.append("trade_date <= ?")
            params.append(end_date)

        sql = f"""
            SELECT factor_name, version, trade_date, symbol, market, factor_value,
                   zscore, rank_pct, industry
            FROM factor_values
            WHERE {' AND '.join(where)}
            ORDER BY trade_date, symbol, factor_name
        """
        conn = self.connect()
        try:
            df = pd.read_sql_query(sql, conn, params=params)
        finally:
            conn.close()
        if pivot and not df.empty:
            return df.pivot_table(
                index=["trade_date", "symbol", "market"],
                columns="factor_name",
                values="factor_value",
                aggfunc="last",
            ).reset_index()
        return df

    def get_factor_matrix(
        self,
        factor_names: Iterable[str],
        *,
        market: str | None = None,
        date: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        value_column: str = "zscore",
        version: str = "v1",
    ) -> pd.DataFrame:
        if value_column not in {"factor_value", "zscore", "rank_pct"}:
            raise ValueError("value_column must be factor_value, zscore, or rank_pct")
        if date:
            start_date = date
            end_date = date
        rows = self.get_factor_values(
            factor_names,
            market=market,
            start_date=start_date,
            end_date=end_date,
            version=version,
        )
        if rows.empty:
            return rows
        return rows.pivot_table(
            index=["trade_date", "symbol", "market"],
            columns="factor_name",
            values=value_column,
            aggfunc="last",
        ).reset_index()

    def upsert_evaluation(
        self,
        factor_name: str,
        *,
        eval_date: str,
        market: str,
        horizon: str,
        version: str = "v1",
        ic: float | None = None,
        rank_ic: float | None = None,
        long_short_return: float | None = None,
        turnover: float | None = None,
        coverage: float | None = None,
        sample_size: int | None = None,
        metrics: dict[str, Any] | None = None,
    ) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        conn = self.connect()
        try:
            conn.execute(
                """
                INSERT INTO factor_evaluations
                    (factor_name, version, eval_date, market, horizon, ic, rank_ic,
                     long_short_return, turnover, coverage, sample_size, metrics_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(factor_name, version, eval_date, market, horizon) DO UPDATE SET
                    ic = excluded.ic,
                    rank_ic = excluded.rank_ic,
                    long_short_return = excluded.long_short_return,
                    turnover = excluded.turnover,
                    coverage = excluded.coverage,
                    sample_size = excluded.sample_size,
                    metrics_json = excluded.metrics_json,
                    updated_at = excluded.updated_at
                """,
                (
                    factor_name,
                    version,
                    eval_date,
                    market,
                    horizon,
                    ic,
                    rank_ic,
                    long_short_return,
                    turnover,
                    coverage,
                    sample_size,
                    json.dumps(metrics or {}, ensure_ascii=False, sort_keys=True),
                    now,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def list_quality(self, market: str | None = None) -> pd.DataFrame:
        where = []
        params: list[Any] = []
        if market:
            where.append("market = ?")
            params.append(market)
        sql = """
            SELECT factor_name, version, as_of_date, market, row_count, non_null_count,
                   missing_rate, mean_value, std_value, min_value, max_value, updated_at
            FROM factor_quality
        """
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY as_of_date DESC, market, factor_name"
        conn = self.connect()
        try:
            return pd.read_sql_query(sql, conn, params=params)
        finally:
            conn.close()

    def record_import_batch(
        self,
        *,
        batch_id: str,
        source: str,
        market: str,
        rows_imported: int,
        started_at: str,
        status: str,
        message: str | None = None,
    ) -> None:
        finished_at = datetime.now().isoformat(timespec="seconds")
        conn = self.connect()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO factor_import_batches
                    (batch_id, source, market, rows_imported, started_at, finished_at, status, message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (batch_id, source, market, rows_imported, started_at, finished_at, status, message),
            )
            conn.commit()
        finally:
            conn.close()

    def list_factors(self) -> pd.DataFrame:
        conn = self.connect()
        try:
            return pd.read_sql_query(
                """
                SELECT d.factor_name, d.category, d.description, d.frequency, d.source,
                       v.version, v.parameters_json, v.formula_hash, d.updated_at
                FROM factor_definitions d
                JOIN factor_versions v ON d.factor_name = v.factor_name
                ORDER BY d.category, d.factor_name, v.version
                """,
                conn,
            )
        finally:
            conn.close()


def build_market_factors(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    required = {"date", "close", "high", "low", "volume"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"market dataframe missing columns: {', '.join(sorted(missing))}")

    frame = df.copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame = frame.dropna(subset=["date"]).sort_values("date")
    for col in ["close", "high", "low", "volume"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")

    close = frame["close"]
    returns = close.pct_change()
    volume = frame["volume"]
    amount_proxy = close * volume
    downside_returns = returns.where(returns < 0, 0)
    rolling_peak = close.rolling(20, min_periods=10).max()
    factors = pd.DataFrame(
        {
            "trade_date": frame["date"].dt.strftime("%Y-%m-%d"),
            "symbol": str(symbol),
            "return_1d": returns,
            "return_5d": close.pct_change(5),
            "momentum_5d": close.pct_change(5),
            "momentum_20d": close.pct_change(20),
            "reversal_5d": -close.pct_change(5),
            "ma_gap_5_20": close.rolling(5).mean() / close.rolling(20).mean() - 1,
            "volatility_20d": returns.rolling(20, min_periods=10).std() * np.sqrt(252),
            "downside_volatility_20d": downside_returns.rolling(20, min_periods=10).std() * np.sqrt(252),
            "max_drawdown_20d": close / rolling_peak - 1,
            "range_pct": (frame["high"] - frame["low"]) / close,
            "volume_zscore_20d": (volume - volume.rolling(20, min_periods=10).mean())
            / volume.rolling(20, min_periods=10).std().replace(0, np.nan),
            "volume_change_5d": volume.pct_change(5),
            "turnover_proxy": amount_proxy,
            "amihud_20d": (returns.abs() / amount_proxy.replace(0, np.nan)).rolling(20, min_periods=10).mean(),
        }
    )
    factors["vmom_20d"] = factors["momentum_20d"] / factors["volatility_20d"].replace(0, np.nan)
    return factors


def register_all_factors(store: FactorStore) -> None:
    for spec in ALL_FACTOR_SPECS:
        store.register_factor(spec)


def register_market_factors(store: FactorStore) -> None:
    register_all_factors(store)


def import_market_factor_frame(
    store: FactorStore,
    factors: pd.DataFrame,
    *,
    market: str,
    version: str = "v1",
) -> int:
    imported = 0
    for spec in MARKET_FACTOR_SPECS:
        values = factors[["trade_date", "symbol", spec.name]].rename(columns={spec.name: "factor_value"})
        imported += store.upsert_values(spec.name, values, version=version, market=market)
        store.record_quality(spec.name, values, version=version, market=market)
    return imported


def import_external_factor_frame(
    store: FactorStore,
    frame: pd.DataFrame,
    spec: FactorSpec,
    *,
    market: str,
) -> int:
    store.register_factor(spec)
    value_column = spec.name if spec.name in frame.columns else "factor_value"
    values = frame[["trade_date", "symbol", value_column] + (["industry"] if "industry" in frame.columns else [])]
    values = values.rename(columns={value_column: "factor_value"})
    imported = store.upsert_values(spec.name, values, version=spec.version, market=market)
    store.record_quality(spec.name, values, version=spec.version, market=market)
    return imported


def _nullable_float(value: Any) -> float | None:
    if pd.isna(value):
        return None
    return float(value)


def _add_in_filter(where: list[str], params: list[Any], column: str, values: Iterable[str] | None) -> None:
    if values is None:
        return
    normalized = [str(value) for value in values]
    if not normalized:
        return
    placeholders = ", ".join("?" for _ in normalized)
    where.append(f"{column} IN ({placeholders})")
    params.extend(normalized)


def _cross_section_zscore(frame: pd.DataFrame, column: str) -> pd.Series:
    values = pd.to_numeric(frame[column], errors="coerce")
    grouped = values.groupby(frame["trade_date"])
    mean = grouped.transform("mean")
    std = grouped.transform(lambda item: item.std(ddof=0))
    return (values - mean) / std.replace(0, np.nan)
