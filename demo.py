"""优惠券计算演示脚本：打印 6 个典型场景的计算结果。

运行：python demo.py
（Windows 下若中文乱码，先执行 chcp 65001）
"""

import sys
from datetime import date
from decimal import Decimal

from coupon import Coupon, CouponError, CouponType, discount, payable

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TODAY = date(2026, 11, 10)


def make(code, kind, threshold, value, start=None, end=None):
    return Coupon(
        code=code,
        type=kind,
        threshold=Decimal(threshold),
        value=Decimal(value),
        start=start or date(2026, 11, 1),
        end=end or date(2026, 12, 31),
    )


def main() -> None:
    cases = [
        ("满100减20，订单 120", make("FULL20", CouponType.FULL_REDUCTION, "100", "20"), "120"),
        ("满100减20，订单 80", make("FULL20", CouponType.FULL_REDUCTION, "100", "20"), "80"),
        ("8.5折，订单 200", make("OFF15", CouponType.DISCOUNT, "100", "0.85"), "200"),
        ("8.5折，订单 1000（触发封顶）", make("OFF15", CouponType.DISCOUNT, "100", "0.85"), "1000"),
        ("无门槛5元，订单 3", make("ANY5", CouponType.NO_THRESHOLD, "0", "5"), "3"),
        (
            "过期券，订单 120",
            make("OLD", CouponType.FULL_REDUCTION, "100", "20", end=date(2026, 10, 31)),
            "120",
        ),
    ]

    print("优惠券计算演示（" + TODAY.isoformat() + "）")
    print("=" * 56)
    for i, (name, coupon, amount) in enumerate(cases, 1):
        try:
            cut = discount(amount, coupon, TODAY)
            pay = payable(amount, coupon, TODAY)
            print(f"{i}. {name}  ->  优惠 {cut}，实付 {pay}")
        except CouponError as exc:
            print(f"{i}. {name}  ->  [拒绝] {exc}")


if __name__ == "__main__":
    main()
