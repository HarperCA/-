"""User-scoped holdings management."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Holding:
    symbol: str
    market: str = "fund"
    username: str = ""
    quantity: float = 0.0
    avg_cost: float = 0.0
    buy_date: str = ""
    notes: str = ""
    added_at: str = ""

    def __post_init__(self) -> None:
        if not self.added_at:
            self.added_at = datetime.now().strftime("%Y-%m-%d %H:%M")


class HoldingsManager:
    """Read and write holdings while keeping each user's data isolated."""

    def __init__(self, filepath: str = "data/holdings.json", username: str = "anonymous"):
        self.filepath = Path(filepath)
        self.username = username or "anonymous"
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self._all_data: Dict[str, List[Holding]] = {}
        self._load()

    def _coerce_holding(self, item: dict, username: str) -> Holding:
        data = dict(item or {})
        data.setdefault("username", username)
        allowed = Holding.__dataclass_fields__.keys()
        data = {key: value for key, value in data.items() if key in allowed}
        holding = Holding(**data)
        if not holding.username:
            holding.username = username
        return holding

    def _load(self) -> None:
        if self.filepath.exists():
            try:
                data = json.loads(self.filepath.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    self._all_data = {
                        "anonymous": [self._coerce_holding(item, "anonymous") for item in data]
                    }
                    self._save()
                elif isinstance(data, dict):
                    self._all_data = {
                        username: [self._coerce_holding(item, username) for item in rows]
                        for username, rows in data.items()
                        if isinstance(rows, list)
                    }
                else:
                    self._all_data = {}
            except Exception:
                self._all_data = {}
        if self.username not in self._all_data:
            self._all_data[self.username] = []

    def _save(self) -> None:
        data = {
            username: [asdict(holding) for holding in holdings]
            for username, holdings in self._all_data.items()
        }
        self.filepath.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    @property
    def holdings(self) -> List[Holding]:
        return self._all_data.get(self.username, [])

    def add(
        self,
        symbol: str,
        market: str = "fund",
        quantity: float = 0,
        avg_cost: float = 0,
        buy_date: str = "",
        notes: str = "",
    ) -> bool:
        self._load()
        symbol = self._normalize_symbol(symbol, market)
        for holding in self.holdings:
            if holding.symbol == symbol and holding.market == market:
                holding.username = self.username
                holding.quantity = quantity
                holding.avg_cost = avg_cost
                holding.buy_date = buy_date or holding.buy_date
                holding.notes = notes or holding.notes
                self._save()
                print(f"Updated holding: {symbol}")
                return True

        self.holdings.append(
            Holding(
                symbol=symbol,
                market=market,
                username=self.username,
                quantity=quantity,
                avg_cost=avg_cost,
                buy_date=buy_date,
                notes=notes,
            )
        )
        self._save()
        print(f"Added holding: {symbol}")
        return True

    def remove(self, symbol: str, market: str = "fund") -> bool:
        self._load()
        symbol = self._normalize_symbol(symbol, market)
        for index, holding in enumerate(self.holdings):
            if holding.symbol == symbol and holding.market == market:
                del self.holdings[index]
                self._save()
                print(f"Removed holding: {symbol}")
                return True
        print(f"Holding not found: {symbol}")
        return False

    def get(self, symbol: str, market: str = "fund") -> Optional[Holding]:
        symbol = self._normalize_symbol(symbol, market)
        for holding in self.holdings:
            if holding.symbol == symbol and holding.market == market:
                return holding
        return None

    def list_all(self) -> List[Holding]:
        return self.holdings

    def is_holding(self, symbol: str, market: str = "fund") -> bool:
        return self.get(symbol, market) is not None

    def generate_diagnosis(self, holding: Holding, df, signals: Dict, ai_report: str = "") -> str:
        latest = df.iloc[-1]
        current_price = float(latest["close"])
        pnl_pct = (current_price - holding.avg_cost) / holding.avg_cost if holding.avg_cost > 0 else 0
        pnl_amount = (current_price - holding.avg_cost) * holding.quantity

        hold_days = 0
        if holding.buy_date:
            try:
                hold_days = (datetime.now() - datetime.strptime(holding.buy_date, "%Y-%m-%d")).days
            except Exception:
                hold_days = 0

        ma_bearish = latest.get("MA10", 0) < latest.get("MA30", 0)
        macd_bearish = latest.get("MACD", 0) < latest.get("MACD_Signal", 0)
        rsi = float(latest.get("RSI", 50))
        reasons = []
        recommendation = "hold"
        urgency = "normal"

        if pnl_pct <= -0.07:
            reasons.append(f"Loss is {pnl_pct * 100:.1f}%, beyond the 7% risk line.")
            recommendation = "consider reducing or stopping loss"
            urgency = "high"
        elif pnl_pct <= -0.05:
            reasons.append(f"Loss is {pnl_pct * 100:.1f}%, close to the risk line.")
            recommendation = "watch closely"
            urgency = "medium"

        if pnl_pct >= 0.15:
            reasons.append(f"Profit is {pnl_pct * 100:.1f}%, consider locking in gains in batches.")
            recommendation = "consider partial take-profit"
            urgency = "medium"

        max_price = float(df["close"].max())
        if holding.avg_cost > 0 and max_price > holding.avg_cost and current_price < max_price * 0.9:
            drawdown = (max_price - current_price) / max_price
            reasons.append(f"Price has pulled back {drawdown * 100:.1f}% from the recent high.")
            if urgency == "normal":
                recommendation = "consider reducing exposure"
                urgency = "medium"

        if ma_bearish and macd_bearish:
            reasons.append("MA and MACD are both weakening.")
            if urgency == "normal":
                recommendation = "wait or reduce"
                urgency = "medium"

        if rsi > 70 and pnl_pct > 0:
            reasons.append("RSI is overbought while the position is profitable.")
        elif rsi < 30:
            reasons.append("RSI is oversold; avoid emotional selling without confirmation.")

        if hold_days < 7 and pnl_pct > 0:
            reasons.append(f"Holding period is only {hold_days} days; redemption costs may matter.")

        if ai_report and ("sell" in ai_report.lower() or "卖出" in ai_report):
            reasons.append("AI report contains a sell signal.")
            if urgency == "normal":
                recommendation = "consider reducing"
                urgency = "medium"

        if not reasons:
            reasons.append("No strong sell signal is detected.")

        lines = [
            "=" * 50,
            f"Holding diagnosis: {holding.symbol} ({holding.market})",
            "=" * 50,
            f"User: {holding.username or self.username}",
            f"Quantity: {holding.quantity}",
            f"Cost: {holding.avg_cost:.4f}",
            f"Latest price: {current_price:.4f}",
            f"Floating P/L: {pnl_pct * 100:+.2f}% ({pnl_amount:+.2f})",
            f"Holding days: {hold_days}",
            "",
            "Signals:",
            f"  MA: {'bearish' if ma_bearish else 'bullish'}",
            f"  MACD: {'bearish' if macd_bearish else 'bullish'}",
            f"  RSI: {rsi:.1f}",
            "",
            "Reasons:",
        ]
        lines.extend(f"  - {reason}" for reason in reasons)
        lines.extend(["", f"Urgency: {urgency}", f"Recommendation: {recommendation}", "=" * 50])
        return "\n".join(lines)

    def generate_sentiment_report(self, holdings_data: List[Dict]) -> str:
        if not holdings_data:
            return ""
        n = len(holdings_data)
        rsi_values = [h.get("rsi", 50) for h in holdings_data if isinstance(h.get("rsi"), (int, float))]
        avg_rsi = sum(rsi_values) / len(rsi_values) if rsi_values else 50
        ma_bull = sum(1 for h in holdings_data if "bull" in str(h.get("ma", "")).lower() or "多头" in str(h.get("ma", "")))
        macd_gold = sum(1 for h in holdings_data if "gold" in str(h.get("macd", "")).lower() or "金叉" in str(h.get("macd", "")))
        profit_count = sum(1 for h in holdings_data if h.get("pnl_pct", 0) > 0)
        score = avg_rsi * 0.6 + (ma_bull / n * 100) * 0.2 + (macd_gold / n * 100) * 0.1 + (profit_count / n * 100) * 0.1
        if score >= 80:
            mood = "extremely hot"
            advice = "Market sentiment is hot; avoid chasing highs."
        elif score >= 60:
            mood = "hot"
            advice = "Sentiment is warm; add positions carefully."
        elif score >= 40:
            mood = "neutral"
            advice = "Sentiment is balanced; follow the plan."
        elif score >= 20:
            mood = "fearful"
            advice = "Sentiment is cool; watch for staged opportunities."
        else:
            mood = "extremely fearful"
            advice = "Panic is elevated; only act with clear risk control."
        return "\n".join(
            [
                "=" * 60,
                "Portfolio sentiment",
                "=" * 60,
                f"Score: {score:.1f}/100 ({mood})",
                f"Average RSI: {avg_rsi:.1f}",
                f"Bullish MA: {ma_bull}/{n}",
                f"MACD gold cross: {macd_gold}/{n}",
                f"Profitable positions: {profit_count}/{n}",
                f"Advice: {advice}",
                "=" * 60,
            ]
        )

    def generate_portfolio_report(self, holdings_data: List[Dict]) -> str:
        if not holdings_data:
            return ""
        n = len(holdings_data)
        total_cost = sum(h["avg_cost"] * h["quantity"] for h in holdings_data)
        total_value = sum(h["current_price"] * h["quantity"] for h in holdings_data)
        total_pnl_amount = sum(h["pnl_amount"] for h in holdings_data)
        total_pnl_pct = (total_pnl_amount / total_cost * 100) if total_cost > 0 else 0
        sorted_by_pnl = sorted(holdings_data, key=lambda item: item["pnl_pct"], reverse=True)
        best = sorted_by_pnl[0]
        worst = sorted_by_pnl[-1]
        rsi_values = [h.get("rsi", 50) for h in holdings_data if isinstance(h.get("rsi"), (int, float))]
        rsi_overbought = sum(1 for value in rsi_values if value > 70)
        max_weight = max(h["current_price"] * h["quantity"] for h in holdings_data) / total_value * 100 if total_value > 0 else 0

        lines = [
            "=" * 60,
            "Portfolio report",
            "=" * 60,
            f"Positions: {n}",
            f"Total cost: {total_cost:.2f}",
            f"Total value: {total_value:.2f}",
            f"Floating P/L: {total_pnl_amount:+.2f} ({total_pnl_pct:+.2f}%)",
            f"Best: {best['symbol']} ({best['pnl_pct']:+.2f}%)",
            f"Worst: {worst['symbol']} ({worst['pnl_pct']:+.2f}%)",
            f"Overbought RSI positions: {rsi_overbought}/{n}",
            f"Largest position weight: {max_weight:.1f}%",
            "",
            "Suggestions:",
        ]
        if max_weight > 50:
            lines.append("- A single position is too concentrated; consider diversification.")
        if rsi_overbought >= n * 0.6:
            lines.append("- Many positions are overbought; avoid aggressive chasing.")
        high_profit = [h for h in holdings_data if h["pnl_pct"] >= 15]
        if high_profit:
            lines.append(f"- {len(high_profit)} positions have profit above 15%; consider staged take-profit.")
        high_loss = [h for h in holdings_data if h["pnl_pct"] <= -7]
        if high_loss:
            lines.append(f"- {len(high_loss)} positions are below -7%; review stop-loss rules.")
        if len(lines) == 12:
            lines.append("- No major portfolio risk concentration detected.")
        lines.append("=" * 60)
        return "\n".join(lines)

    @staticmethod
    def _normalize_symbol(symbol: str, market: str) -> str:
        symbol = (symbol or "").strip()
        return symbol.zfill(6) if market in ("a_stock", "fund") else symbol.upper()
