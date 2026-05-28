"""
Paper trading engine.

Receives orders, runs risk checks, simulates fills, updates the account,
and executes circuit-breaker actions such as halt, reduce, and clear.
"""
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import json

from core.console import configure_console_output
from .order import Order, OrderSide, OrderStatus, OrderType
from .portfolio import Portfolio, Position
from .risk_manager import RiskManager

configure_console_output()


class PaperTrader:
    """Paper-trading engine for simulated execution."""

    def __init__(
        self,
        initial_cash: float = 100000.0,
        commission_rate: float = 0.0003,
        min_commission: float = 5.0,
        slippage: float = 0.001,
        risk_manager: RiskManager = None,
    ):
        self.portfolio = Portfolio.load("portfolio.json")
        if self.portfolio.initial_cash != initial_cash and self.portfolio.total_value == 0:
            self.portfolio = Portfolio(initial_cash=initial_cash)
        self.commission_rate = commission_rate
        self.min_commission = min_commission
        self.slippage = slippage
        self.risk = risk_manager or RiskManager()
        self.order_log: List[Order] = []
        self.daily_stats: Dict[str, dict] = {}

    def get_market_price(self, symbol: str, side: OrderSide) -> float:
        """Get a simulated market price with slippage."""
        pos = self.portfolio.get_position(symbol)
        if not pos or pos.current_price <= 0:
            raise ValueError(f"无法获取 {symbol} 的市场价格，请先调用 update_prices()")

        if side == OrderSide.BUY:
            return pos.current_price * (1 + self.slippage)
        return pos.current_price * (1 - self.slippage)

    def update_prices(self, prices: Dict[str, float]):
        """Update market prices for open positions."""
        self.portfolio.update_market_prices(prices)
        self.portfolio.record_peak()

    def submit_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: int,
        price: Optional[float] = None,
        reason: str = "",
        force: bool = False,
    ) -> Order:
        """Submit an order and return the simulated order result."""
        order_type = OrderType.LIMIT if price else OrderType.MARKET
        order = Order(
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type,
            price=price,
            reason=reason,
        )

        passed, msg = self.risk.check_before_order(order, self.portfolio, force=force)
        if not passed:
            order.status = OrderStatus.REJECTED
            order.reason += f" | 风控拒绝: {msg}"
            self.risk.violations.append(f"{symbol} {side.value}被拒: {msg}")
            self.order_log.append(order)
            print(f"订单被拒: {msg}")
            return order

        try:
            fill_price = price if price else self.get_market_price(symbol, side)
        except ValueError as exc:
            order.status = OrderStatus.REJECTED
            order.reason += f" | 价格获取失败: {exc}"
            self.order_log.append(order)
            print(exc)
            return order

        trade_value = quantity * fill_price
        commission = max(trade_value * self.commission_rate, self.min_commission)

        if side == OrderSide.BUY:
            total_cost = trade_value + commission
            if total_cost > self.portfolio.cash:
                order.status = OrderStatus.REJECTED
                order.reason += f" | 资金不足: 需{total_cost:.2f}, 可用{self.portfolio.cash:.2f}"
                self.order_log.append(order)
                print(f"资金不足: 需{total_cost:.2f}, 可用{self.portfolio.cash:.2f}")
                return order

        if side == OrderSide.SELL:
            pos = self.portfolio.get_position(symbol)
            if not pos or pos.quantity < quantity:
                order.status = OrderStatus.REJECTED
                held = pos.quantity if pos else 0
                order.reason += f" | 持仓不足: 持{held}, 卖{quantity}"
                self.order_log.append(order)
                print(f"持仓不足: 持{held}, 卖{quantity}")
                return order

        order.fill_price = fill_price
        order.fill_time = datetime.now()
        order.status = OrderStatus.FILLED

        if side == OrderSide.BUY:
            self.portfolio.cash -= trade_value + commission
        else:
            self.portfolio.cash += trade_value - commission

        self.portfolio.total_commission += commission

        if symbol not in self.portfolio.positions:
            self.portfolio.positions[symbol] = Position(symbol=symbol)

        if side == OrderSide.BUY:
            cost_with_fee = (trade_value + commission) / quantity
            self.portfolio.positions[symbol].add(quantity, cost_with_fee)
        else:
            self.portfolio.positions[symbol].add(-quantity, fill_price)

        self.portfolio.positions[symbol].update_price(fill_price)
        self.order_log.append(order)
        self.risk.record_order(order)
        self.portfolio.save()

        action = "买入" if side == OrderSide.BUY else "卖出"
        print(f"{action}成交 {symbol} | {quantity}股 @ {fill_price:.2f} | 手续费 {commission:.2f} | 理由: {reason}")
        return order

    def close_position(self, symbol: str, reason: str = "平仓", force: bool = False) -> Optional[Order]:
        """Close the full position for one symbol."""
        pos = self.portfolio.get_position(symbol)
        if not pos or pos.quantity == 0:
            print(f"{symbol} 无持仓，无需平仓")
            return None
        return self.submit_order(
            symbol=symbol,
            side=OrderSide.SELL,
            quantity=abs(pos.quantity),
            reason=reason,
            force=force,
        )

    def close_all(self, reason: str = "清仓", force: bool = False):
        """Close all open positions."""
        symbols = [symbol for symbol, pos in self.portfolio.positions.items() if pos.quantity != 0]
        for symbol in symbols:
            self.close_position(symbol, reason, force=force)

    def reduce_positions(self, target_position_pct: float = 0.50, reason: str = "风控减仓"):
        """Reduce every open long position to a target percentage of current shares."""
        target_position_pct = max(0.0, min(1.0, target_position_pct))
        for symbol, pos in list(self.portfolio.positions.items()):
            if pos.quantity <= 0:
                continue
            sell_qty = int(pos.quantity * (1 - target_position_pct))
            if sell_qty <= 0:
                sell_qty = pos.quantity
            self.submit_order(
                symbol=symbol,
                side=OrderSide.SELL,
                quantity=sell_qty,
                reason=reason,
                force=True,
            )

    def _cancel_pending_orders(self, reason: str):
        """Cancel local pending orders after a halt."""
        for order in self.order_log:
            if order.status == OrderStatus.PENDING:
                order.status = OrderStatus.CANCELLED
                order.reason += f" | {reason}"

    def run_risk_check(self) -> List[str]:
        """Run portfolio checks and execute pending circuit-breaker actions."""
        alerts = self.risk.check_portfolio_risk(self.portfolio)
        if alerts:
            print("\n".join(["警告 " + alert for alert in alerts]))

        action = self.risk.consume_pending_action()
        if action == "clear":
            self.close_all("风控熔断风险保护处理", force=True)
        elif action == "reduce":
            self.reduce_positions(0.50, "风控熔断风险保护处理")
        elif action == "halt":
            self._cancel_pending_orders("风控熔断自动撤单")
        return alerts

    def get_trade_summary(self) -> str:
        """Generate a trade summary."""
        filled = [order for order in self.order_log if order.status == OrderStatus.FILLED]
        rejected = [order for order in self.order_log if order.status == OrderStatus.REJECTED]

        lines = ["=" * 50, "模拟盘交易摘要", "=" * 50]
        lines.append(str(self.portfolio.to_dict()))
        lines.append("")
        lines.append(f"总订单: {len(self.order_log)} | 成交: {len(filled)} | 拒绝: {len(rejected)}")

        if filled:
            lines.append("")
            lines.append("近期成交记录:")
            for order in filled[-5:]:
                lines.append(f"  {order.side.value} {order.symbol} {order.quantity}股 @ {order.fill_price:.2f} [{order.reason}]")

        lines.append("")
        lines.append(self.risk.generate_risk_report(self.portfolio))
        return "\n".join(lines)

    def save_state(self, filepath: str = "paper_trading_state.json"):
        """Save paper-trading state."""
        data = {
            "portfolio": self.portfolio.to_dict(),
            "orders": [order.to_dict() for order in self.order_log],
            "save_time": datetime.now().isoformat(),
        }
        Path(filepath).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"模拟盘状态已保存: {filepath}")
