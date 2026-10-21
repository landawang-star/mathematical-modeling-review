#!/usr/bin/env python3
"""Map the Skill's 0–100 diagnostic score to its non-official award forecast."""

import json
import sys
from decimal import Decimal, InvalidOperation


TIERS = (
    (Decimal("84"), "国一", "国一"),
    (Decimal("78"), "国二", "国二至国一"),
    (Decimal("75"), "省一", "省一至国二"),
    (Decimal("70"), "省二", "省二至省一"),
    (Decimal("60"), "省三", "省三至省二"),
    (Decimal("0"), "暂不预估省级奖", "暂不预估省级奖至省三"),
)


def predict(total):
    if isinstance(total, bool) or not isinstance(total, (int, float, Decimal)):
        raise ValueError("total must be a number from 0 to 100")
    try:
        value = Decimal(str(total))
    except InvalidOperation as exc:
        raise ValueError("total is not a valid number") from exc
    if not value.is_finite() or not Decimal("0") <= value <= Decimal("100"):
        raise ValueError("total must be between 0 and 100")
    for minimum, forecast, interval in TIERS:
        if value >= minimum:
            return {
                "total": float(value),
                "forecast": forecast,
                "interval": interval,
                "note": "非官方经验预测；仅适用于五维均已评分的完整 CUMCM 评审",
            }
    raise AssertionError("unreachable")


def main(argv):
    if len(argv) != 2:
        print("usage: python3 scripts/award.py TOTAL", file=sys.stderr)
        return 2
    try:
        result = predict(Decimal(argv[1]))
    except (InvalidOperation, ValueError) as exc:
        print(f"award error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
