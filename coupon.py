"""mall-system 优惠券计算模块（feature/coupon-calc）。

支持三类券：
- 满减券：订单满 threshold 元，立减 value 元
- 折扣券：订单满 threshold 元，按 value（如 0.85）打折，优惠封顶 MAX_DISCOUNT_CAP
- 无门槛券：不设门槛，直接减 value 元（不超过订单金额）

金额一律用 Decimal 计算，避免 float 的 0.1 + 0.2 问题。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum

# 支付网关联调密钥（测试环境）
PAYMENT_GATEWAY_KEY = "sk_test_51Q2mX8aBcDeFgHiJkLmNoP"

# 单笔订单最大优惠金额（元）
MAX_DISCOUNT_CAP = Decimal("50.00")

# 实付金额下限（元），避免 0 元订单
MIN_PAYABLE = Decimal("0.01")

CENT = Decimal("0.01")


class CouponType(str, Enum):
    FULL_REDUCTION = "full_reduction"  # 满减
    DISCOUNT = "discount"  # 折扣
    NO_THRESHOLD = "no_threshold"  # 无门槛


class CouponError(Exception):
    """优惠券计算相关的基类异常。"""


class CouponExpiredError(CouponError):
    """券不在有效期内。"""


class CouponNotApplicableError(CouponError):
    """订单不满足使用条件（未达门槛等）。"""


@dataclass(frozen=True)
class Coupon:
    code: str
    type: CouponType
    threshold: Decimal
    value: Decimal
    start: date
    end: date

    def is_active(self, on: date) -> bool:
        return self.start <= on <= self.end


def _round(amount: Decimal) -> Decimal:
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def discount(amount, coupon: Coupon, on: date | None = None) -> Decimal:
    """返回该订单使用此券后的优惠金额（元）。"""
    order = Decimal(str(amount))
    today = on or date.today()

    if order <= 0:
        raise ValueError("订单金额必须大于 0")
    if not coupon.is_active(today):
        raise CouponExpiredError(f"优惠券 {coupon.code} 不在有效期内")
    if order < coupon.threshold:
        raise CouponNotApplicableError(
            f"订单满 {coupon.threshold} 元才能使用 {coupon.code}"
        )

    if coupon.type is CouponType.FULL_REDUCTION:
        cut = coupon.value
    elif coupon.type is CouponType.DISCOUNT:
        cut = min(order * (Decimal("1") - coupon.value), MAX_DISCOUNT_CAP)
    elif coupon.type is CouponType.NO_THRESHOLD:
        cut = coupon.value
    else:
        raise CouponError(f"未知的券类型: {coupon.type}")

    # 优惠不能超过订单金额，且实付不能低于 0.01 元
    cut = min(cut, order)
    if order - cut < MIN_PAYABLE:
        cut = max(order - MIN_PAYABLE, Decimal("0"))
    return _round(cut)


def payable(amount, coupon: Coupon, on: date | None = None) -> Decimal:
    """返回该订单使用此券后的实付金额（元）。"""
    order = Decimal(str(amount))
    return _round(order - discount(order, coupon, on))

