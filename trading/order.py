"""
订单定义模块
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class OrderSide(Enum):
    """订单方向"""
    BUY = "买入"
    SELL = "卖出"


class OrderType(Enum):
    """订单类型"""
    MARKET = "市价单"      # 以当前市场价格成交
    LIMIT = "限价单"       # 以指定价格或更好价格成交


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "待成交"
    FILLED = "已成交"
    PARTIAL = "部分成交"
    CANCELLED = "已撤销"
    REJECTED = "已拒绝"


@dataclass
class Order:
    """订单对象"""
    symbol: str                         # 标的代码
    side: OrderSide                     # 买入/卖出
    quantity: int                       # 数量（股）
    order_type: OrderType = OrderType.MARKET  # 市价/限价
    price: Optional[float] = None       # 限价单的价格
    status: OrderStatus = OrderStatus.PENDING
    create_time: datetime = field(default_factory=datetime.now)
    fill_time: Optional[datetime] = None
    fill_price: Optional[float] = None  # 实际成交价格
    order_id: str = field(default_factory=lambda: f"ORD{datetime.now().strftime('%Y%m%d%H%M%S%f')[:20]}")
    reason: str = ""                    # 下单理由/策略信号

    def __post_init__(self):
        if self.order_type == OrderType.LIMIT and self.price is None:
            raise ValueError("限价单必须指定价格")
        if self.quantity <= 0:
            raise ValueError("下单数量必须大于0")

    def to_dict(self) -> dict:
        return {
            "订单号": self.order_id,
            "标的": self.symbol,
            "方向": self.side.value,
            "类型": self.order_type.value,
            "数量": self.quantity,
            "委托价": self.price if self.price else "市价",
            "成交价": self.fill_price,
            "状态": self.status.value,
            "下单时间": self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "成交时间": self.fill_time.strftime("%Y-%m-%d %H:%M:%S") if self.fill_time else None,
            "理由": self.reason,
        }
