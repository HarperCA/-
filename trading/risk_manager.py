"""
Risk management module.

Includes position limits, stop loss/take profit, max drawdown controls,
daily loss controls, abnormal order checks, and circuit-breaker actions.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from .order import Order, OrderSide
from .portfolio import Portfolio


@dataclass
class RiskConfig:
    """Risk configuration parameters."""

    # Position controls
    max_position_pct: float = 0.20
    max_total_positions: int = 10
    min_cash_ratio: float = 0.10

    # Stop loss / take profit
    stop_loss_pct: float = 0.07
    take_profit_pct: float = 0.15
    trailing_stop_pct: float = 0.10

    # Portfolio controls
    max_daily_loss_pct: float = 0.03
    max_drawdown_pct: float = 0.15
    drawdown_action: str = "halt"  # halt/reduce/clear

    # Trading frequency
    max_orders_per_day: int = 20
    cooldown_minutes: int = 5

    # Circuit breaker controls
    circuit_breaker_enabled: bool = True
    circuit_breaker_action: str = "halt"  # halt/reduce/clear
    max_volatility_pct: float = 0.08
    max_extreme_move_pct: float = 0.10
    max_order_price_deviation_pct: float = 0.05


class RiskManager:
    """Risk engine for pre-order checks and live portfolio monitoring."""

    def __init__(self, config: RiskConfig = None):
        self.config = config or RiskConfig()
        self.today_orders: List[Order] = []
        self.last_order_time: Dict[str, datetime] = {}
        self.violations: List[str] = []
        self.is_halted: bool = False
        self.pending_action: Optional[str] = None
        self.last_circuit_reason: Optional[str] = None

    def reset_daily(self):
        """Reset daily counters."""
        self.today_orders = []
        self.violations = []
        if self.is_halted:
            self.violations.append("[系统] 交易暂停中，需要手动恢复")

    def resume_trading(self):
        """Manually resume trading."""
        self.is_halted = False
        self.pending_action = None
        self.last_circuit_reason = None
        self.violations.append("[系统] 交易已恢复")

    def _trigger_circuit_breaker(self, reason: str, action: Optional[str] = None) -> str:
        """Enter protected mode and request halt/reduce/clear execution."""
        if not self.config.circuit_breaker_enabled:
            return "none"

        action = action or self.config.circuit_breaker_action
        if action not in {"halt", "reduce", "clear"}:
            action = "halt"

        self.is_halted = True
        self.pending_action = action
        self.last_circuit_reason = reason

        message = f"[熔断] {reason}，动作={action}"
        if not self.violations or self.violations[-1] != message:
            self.violations.append(message)
        return action

    def consume_pending_action(self) -> Optional[str]:
        """Return and clear the pending circuit-breaker action."""
        action = self.pending_action
        self.pending_action = None
        return action

    def check_before_order(
        self,
        order: Order,
        portfolio: Portfolio,
        force: bool = False,
    ) -> Tuple[bool, str]:
        """
        Check an order before submission.

        Forced risk-reduction orders bypass normal halt/cooldown/frequency gates.
        """
        cfg = self.config
        symbol = order.symbol
        pos = portfolio.get_position(symbol)

        if force:
            if order.side != OrderSide.SELL:
                return False, "强制风控指令仅允许降低风险暴露"
            return True, "强制风控指令通过"

        if self.is_halted and order.side == OrderSide.BUY:
            return False, "交易已暂停（触发熔断/止损风控）"

        ref_price = pos.current_price if pos else 0
        if (
            cfg.circuit_breaker_enabled
            and order.price
            and ref_price > 0
            and abs(order.price - ref_price) / ref_price >= cfg.max_order_price_deviation_pct
        ):
            action = self._trigger_circuit_breaker(
                f"异常交易检测：{symbol} 限价偏离当前价 {abs(order.price - ref_price) / ref_price * 100:.1f}%"
            )
            return False, f"异常交易触发熔断，动作={action}"

        if len(self.today_orders) >= cfg.max_orders_per_day:
            return False, f"单日下单次数超限（{cfg.max_orders_per_day}次）"

        if symbol in self.last_order_time:
            elapsed = (datetime.now() - self.last_order_time[symbol]).total_seconds() / 60
            if elapsed < cfg.cooldown_minutes:
                wait = cfg.cooldown_minutes - int(elapsed)
                return False, f"冷却时间未过，需要等待 {wait} 分钟"

        if order.side == OrderSide.BUY:
            order_price = order.price or (pos.current_price if pos else 0)
            estimated_cost = order.quantity * order_price
            if portfolio.cash - estimated_cost < portfolio.total_value * cfg.min_cash_ratio:
                return False, f"现金不足，需保留至少 {cfg.min_cash_ratio * 100:.0f}% 现金"

            current_mv = pos.market_value if pos else 0
            added_mv = order.quantity * order_price
            if current_mv + added_mv > portfolio.total_value * cfg.max_position_pct:
                max_allowed = int((portfolio.total_value * cfg.max_position_pct - current_mv) / (order_price or 1))
                return False, f"单标仓位将超限（最大{cfg.max_position_pct * 100:.0f}%），最多可再买 {max_allowed} 股"

            if pos is None or pos.quantity == 0:
                current_count = len([p for p in portfolio.positions.values() if p.quantity != 0])
                if current_count >= cfg.max_total_positions:
                    return False, f"持仓数量已达上限（{cfg.max_total_positions}只）"

        if portfolio.daily_pnl < -portfolio.initial_cash * cfg.max_daily_loss_pct:
            action = self._trigger_circuit_breaker(
                f"当日亏损 {abs(portfolio.daily_pnl) / portfolio.initial_cash * 100:.1f}% 超过上限 {cfg.max_daily_loss_pct * 100:.1f}%"
            )
            return False, f"单日亏损已达上限（{cfg.max_daily_loss_pct * 100:.0f}%），动作={action}"

        return True, "通过"

    def check_portfolio_risk(self, portfolio: Portfolio) -> List[str]:
        """Check portfolio risk and return alert messages."""
        alerts: List[str] = []
        cfg = self.config

        for symbol, pos in portfolio.positions.items():
            if pos.quantity == 0:
                continue

            pnl_pct = pos.unrealized_pnl_pct

            if pnl_pct <= -cfg.stop_loss_pct:
                alerts.append(f"[止损] {symbol} 亏损达 {pnl_pct * 100:.1f}%，请复核仓位暴露和风险承受能力")
                if cfg.circuit_breaker_action in {"reduce", "clear"}:
                    action = self._trigger_circuit_breaker(
                        f"{symbol} 亏损 {abs(pnl_pct) * 100:.1f}% 达到止损线"
                    )
                    alerts.append(f"[熔断] 已触发自动{action}")

            if pnl_pct >= cfg.take_profit_pct:
                alerts.append(f"[止盈] {symbol} 盈利达 {pnl_pct * 100:.1f}%，请复核收益是否稳定以及仓位是否过重")

            if pnl_pct <= -cfg.max_extreme_move_pct:
                action = self._trigger_circuit_breaker(
                    f"极端行情：{symbol} 相对成本下跌 {abs(pnl_pct) * 100:.1f}%"
                )
                alerts.append(f"[熔断] {symbol} 极端跌幅触发自动{action}")

            if pos.max_price > 0 and pos.current_price < pos.max_price * (1 - cfg.trailing_stop_pct):
                dd_from_peak = (pos.max_price - pos.current_price) / pos.max_price
                alerts.append(f"[移动止损] {symbol} 从高点回撤 {dd_from_peak * 100:.1f}%，请复核回撤是否继续扩大")

            if pos.max_price > 0 and pos.min_price != float("inf"):
                volatility = (pos.max_price - pos.min_price) / pos.max_price
                if volatility >= cfg.max_volatility_pct:
                    action = self._trigger_circuit_breaker(
                        f"波动异常：{symbol} 持仓期高低波幅 {volatility * 100:.1f}%"
                    )
                    alerts.append(f"[熔断] {symbol} 波动异常触发自动{action}")

        if portfolio.drawdown >= cfg.max_drawdown_pct:
            alerts.append(f"[重大回撤] 账户回撤 {portfolio.drawdown * 100:.1f}%，触发风控！")
            action = self._trigger_circuit_breaker(
                f"账户回撤 {portfolio.drawdown * 100:.1f}% 超过上限 {cfg.max_drawdown_pct * 100:.1f}%",
                cfg.drawdown_action,
            )
            if action == "halt":
                alerts.append("[系统] 已自动暂停新交易，请检查策略或手动恢复")
            elif action == "clear":
                alerts.append("[系统] 已触发极端风险保护，请人工复核全部持仓暴露")
            elif action == "reduce":
                alerts.append("[系统] 已触发风险保护处理，请复核目标风险水平")

        return alerts

    def record_order(self, order: Order):
        """Record an executed order."""
        self.today_orders.append(order)
        self.last_order_time[order.symbol] = datetime.now()

    def generate_risk_report(self, portfolio: Portfolio) -> str:
        """Generate a text risk report."""
        lines = ["=" * 40, "风控报告", "=" * 40]
        lines.append(f"交易暂停状态: {'是' if self.is_halted else '否'}")
        lines.append(f"熔断原因: {self.last_circuit_reason or '无'}")
        lines.append(f"待执行动作: {self.pending_action or '无'}")
        lines.append(f"今日下单数: {len(self.today_orders)} / {self.config.max_orders_per_day}")
        lines.append(f"账户回撤: {portfolio.drawdown * 100:.2f}%")
        lines.append("")

        alerts = self.check_portfolio_risk(portfolio)
        if alerts:
            lines.append("风险告警:")
            for alert in alerts:
                lines.append(f"  - {alert}")
        else:
            lines.append("暂无风险告警")

        if self.violations:
            lines.append("")
            lines.append("今日违规记录:")
            for violation in self.violations[-5:]:
                lines.append(f"  - {violation}")

        lines.append("=" * 40)
        return "\n".join(lines)
