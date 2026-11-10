"""优惠券计算模块的单元测试。

运行：python -m unittest discover -s tests -t . -v
"""

import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from coupon import (
    Coupon,
    CouponExpiredError,
    CouponNotApplicableError,
    CouponType,
    discount,
    payable,
)

TODAY = date(2026, 11, 10)
ROOT = Path(__file__).resolve().parent.parent


def make(kind, threshold="0", value="0", start=None, end=None):
    return Coupon(
        code="TEST",
        type=kind,
        threshold=Decimal(threshold),
        value=Decimal(value),
        start=start or date(2026, 11, 1),
        end=end or date(2026, 12, 31),
    )


class DiscountTest(unittest.TestCase):
    def test_full_reduction(self):
        coupon = make(CouponType.FULL_REDUCTION, "100", "20")
        self.assertEqual(discount("120", coupon, TODAY), Decimal("20.00"))
        self.assertEqual(payable("120", coupon, TODAY), Decimal("100.00"))

    def test_full_reduction_below_threshold(self):
        coupon = make(CouponType.FULL_REDUCTION, "100", "20")
        with self.assertRaises(CouponNotApplicableError):
            discount("99.99", coupon, TODAY)

    def test_discount_rate(self):
        coupon = make(CouponType.DISCOUNT, "100", "0.85")
        self.assertEqual(discount("200", coupon, TODAY), Decimal("30.00"))
        self.assertEqual(payable("200", coupon, TODAY), Decimal("170.00"))

    def test_discount_hits_cap(self):
        coupon = make(CouponType.DISCOUNT, "100", "0.85")
        self.assertEqual(discount("1000", coupon, TODAY), Decimal("50.00"))

    def test_no_threshold_keeps_min_payable(self):
        coupon = make(CouponType.NO_THRESHOLD, "0", "5")
        self.assertEqual(discount("3", coupon, TODAY), Decimal("2.99"))
        self.assertEqual(payable("3", coupon, TODAY), Decimal("0.01"))

    def test_expired_coupon(self):
        coupon = make(CouponType.FULL_REDUCTION, "100", "20", end=date(2026, 10, 31))
        with self.assertRaises(CouponExpiredError):
            discount("120", coupon, TODAY)

    def test_invalid_amount(self):
        coupon = make(CouponType.FULL_REDUCTION, "100", "20")
        for bad in ("0", "-1", "-0.01"):
            with self.assertRaises(ValueError):
                discount(bad, coupon, TODAY)

    def test_decimal_precision(self):
        coupon = make(CouponType.DISCOUNT, "0", "0.9")
        self.assertEqual(discount("0.1", coupon, TODAY), Decimal("0.01"))
        self.assertEqual(payable("0.1", coupon, TODAY), Decimal("0.09"))


class SecretHygieneTest(unittest.TestCase):
    def test_no_hardcoded_gateway_key(self):
        source = (ROOT / "coupon.py").read_text(encoding="utf-8")
        self.assertNotIn("sk_test_", source, "支付密钥不应硬编码在源码中")


if __name__ == "__main__":
    unittest.main()
