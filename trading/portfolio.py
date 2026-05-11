"""
账户与持仓管理
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional
import json
from pathlib import Path


@dataclass
class Position:
    """持仓对象"""
    symbol: str
    quantity: int = 0                   # 持仓数量（正=多仓，负=空仓）
    avg_cost: float = 0.0               # 平均成本价
    current_price: float = 0.0          # 当前市场价
    max_price: float = 0.0              # 持仓期间最高价（用于移动止损）
    min_price: float = float('inf')     # 持仓期间最低价
    open_time: datetime = field(default_factory=datetime.now)

    @property
    def market_value(self) -> float:
        """持仓市值"""
        return self.quantity * self.current_price

    @property
    def cost_basis(self) -> float:
        """成本 basis"""
        return self.quantity * self.avg_cost

    @property
    def unrealized_pnl(self) -> float:
        """浮动盈亏"""
        return self.quantity * (self.current_price - self.avg_cost)

    @property
    def unrealized_pnl_pct(self) -> float:
        """浮动盈亏百分比"""
        if self.avg_cost == 0:
            return 0.0
        return (self.current_price - self.avg_cost) / self.avg_cost

    def update_price(self, price: float):
        """更新最新价格"""
        self.current_price = price
        self.max_price = max(self.max_price, price)
        self.min_price = min(self.min_price, price)

    def add(self, quantity: int, price: float):
        """加仓/减仓（quantity为正表示买入，为负表示卖出）"""
        if quantity == 0:
            return
        # 计算新的平均成本
        total_cost = self.cost_basis + quantity * price
        total_qty = self.quantity + quantity
        if total_qty != 0:
            self.avg_cost = total_cost / total_qty
        else:
            self.avg_cost = 0.0
        self.quantity = total_qty

    def to_dict(self) -> dict:
        return {
            "标的": self.symbol,
            "持仓量": self.quantity,
            "成本价": round(self.avg_cost, 4),
            "当前价": round(self.current_price, 4),
            "市值": round(self.market_value, 2),
            "浮动盈亏": round(self.unrealized_pnl, 2),
            "盈亏比例": f"{self.unrealized_pnl_pct*100:.2f}%",
            "持仓天数": (datetime.now() - self.open_time).days,
        }


@dataclass
class Portfolio:
    """投资组合/账户"""
    initial_cash: float = 100000.0
    cash: float = 100000.0              # 可用现金
    positions: Dict[str, Position] = field(default_factory=dict)
    total_commission: float = 0.0       # 累计手续费
    trade_history: list = field(default_factory=list)

    # 风控相关
    daily_pnl: float = 0.0              # 当日盈亏
    max_value: float = 100000.0         # 历史最高净值（用于计算回撤）
    peak_date: Optional[datetime] = None

    def update_market_prices(self, prices: Dict[str, float]):
        """更新所有持仓的市场价格"""
        for symbol, price in prices.items():
            if symbol in self.positions:
                self.positions[symbol].update_price(price)

    @property
    def total_market_value(self) -> float:
        """持仓总市值"""
        return sum(pos.market_value for pos in self.positions.values())

    @property
    def total_value(self) -> float:
        """账户总净值 = 现金 + 持仓市值"""
        return self.cash + self.total_market_value

    @property
    def total_return(self) -> float:
        """总收益率"""
        return (self.total_value - self.initial_cash) / self.initial_cash

    @property
    def total_unrealized_pnl(self) -> float:
        """总浮动盈亏"""
        return sum(pos.unrealized_pnl for pos in self.positions.values())

    @property
    def drawdown(self) -> float:
        """当前回撤"""
        if self.max_value == 0:
            return 0.0
        return (self.max_value - self.total_value) / self.max_value

    def record_peak(self):
        """记录净值新高"""
        if self.total_value > self.max_value:
            self.max_value = self.total_value
            self.peak_date = datetime.now()

    def get_position(self, symbol: str) -> Optional[Position]:
        """获取某个标的的持仓"""
        return self.positions.get(symbol)

    def to_dict(self) -> dict:
        return {
            "账户净值": round(self.total_value, 2),
            "可用现金": round(self.cash, 2),
            "持仓市值": round(self.total_market_value, 2),
            "总收益率": f"{self.total_return*100:.2f}%",
            "浮动盈亏": round(self.total_unrealized_pnl, 2),
            "累计手续费": round(self.total_commission, 2),
            "当前回撤": f"{self.drawdown*100:.2f}%",
            "持仓数量": len([p for p in self.positions.values() if p.quantity != 0]),
        }

    def save(self, filepath: str = "portfolio.json"):
        """保存账户状态到文件"""
        data = {
            "initial_cash": self.initial_cash,
            "cash": self.cash,
            "total_commission": self.total_commission,
            "max_value": self.max_value,
            "positions": {
                s: {
                    "symbol": p.symbol,
                    "quantity": p.quantity,
                    "avg_cost": p.avg_cost,
                    "current_price": p.current_price,
                    "open_time": p.open_time.isoformat() if isinstance(p.open_time, datetime) else str(p.open_time),
                }
                for s, p in self.positions.items() if p.quantity != 0
            },
            "update_time": datetime.now().isoformat(),
        }
        Path(filepath).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, filepath: str = "portfolio.json") -> "Portfolio":
        """从文件加载账户状态"""
        if not Path(filepath).exists():
            return cls()
        data = json.loads(Path(filepath).read_text(encoding="utf-8"))
        p = cls(
            initial_cash=data.get("initial_cash", 100000),
            cash=data.get("cash", 100000),
            total_commission=data.get("total_commission", 0),
            max_value=data.get("max_value", 100000),
        )
        # 恢复持仓
        for symbol, pos_data in data.get("positions", {}).items():
            try:
                pos = Position(
                    symbol=pos_data["symbol"],
                    quantity=pos_data["quantity"],
                    avg_cost=pos_data["avg_cost"],
                    current_price=pos_data.get("current_price", 0),
                    open_time=datetime.fromisoformat(pos_data["open_time"]) if "open_time" in pos_data else datetime.now(),
                )
                p.positions[symbol] = pos
            except Exception:
                pass
        return p
