import unittest

from trading.order import Order, OrderSide
from trading.paper_trading import PaperTrader
from trading.portfolio import Portfolio, Position
from trading.risk_manager import RiskConfig, RiskManager


class RiskManagerCircuitBreakerTest(unittest.TestCase):
    def make_portfolio(self):
        portfolio = Portfolio(initial_cash=100000, cash=90000, max_value=100000)
        position = Position(symbol="TEST", quantity=100, avg_cost=100, current_price=100)
        position.max_price = 100
        position.min_price = 100
        portfolio.positions["TEST"] = position
        return portfolio

    def test_abnormal_limit_price_triggers_halt(self):
        portfolio = self.make_portfolio()
        risk = RiskManager(
            RiskConfig(
                max_order_price_deviation_pct=0.05,
                circuit_breaker_action="halt",
            )
        )
        order = Order(symbol="TEST", side=OrderSide.BUY, quantity=10, price=110)

        passed, message = risk.check_before_order(order, portfolio)

        self.assertFalse(passed)
        self.assertTrue(risk.is_halted)
        self.assertEqual(risk.pending_action, "halt")
        self.assertIn("异常交易", message)

    def test_extreme_move_requests_clear(self):
        portfolio = self.make_portfolio()
        portfolio.positions["TEST"].update_price(88)
        risk = RiskManager(
            RiskConfig(
                circuit_breaker_action="clear",
                max_extreme_move_pct=0.10,
            )
        )

        alerts = risk.check_portfolio_risk(portfolio)

        self.assertTrue(risk.is_halted)
        self.assertEqual(risk.pending_action, "clear")
        self.assertTrue(any("极端跌幅" in alert for alert in alerts))

    def test_paper_trader_executes_clear_action_with_forced_sell(self):
        portfolio = self.make_portfolio()
        portfolio.positions["TEST"].update_price(88)
        portfolio.save = lambda *args, **kwargs: None

        trader = PaperTrader(
            initial_cash=100000,
            risk_manager=RiskManager(
                RiskConfig(
                    circuit_breaker_action="clear",
                    max_extreme_move_pct=0.10,
                )
            ),
        )
        trader.portfolio = portfolio

        trader.run_risk_check()

        self.assertEqual(trader.portfolio.positions["TEST"].quantity, 0)


if __name__ == "__main__":
    unittest.main()
