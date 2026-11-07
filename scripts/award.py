#!/usr/bin/env python3
"""Map a 0–100 diagnostic score to the Skill's two-stage forecast."""

import json
import sys
from decimal import Decimal, InvalidOperation


TIERS = (
    (Decimal("84"), "国一", "国二至国一", ("国二", "国一")),
    (Decimal("78"), "国二", "省一至国一", ("省一", "国二", "国一")),
    (Decimal("70"), "省一", "省二至国二", ("省二", "省一", "国二")),
    (Decimal("65"), "省二", "省三至省一", ("省三", "省二", "省一")),
    (Decimal("60"), "省三", "不获奖至省二", ("不获奖", "省三", "省二")),
    (Decimal("0"), "不获奖", "不获奖至省三", ("不获奖", "省三")),
)

NATIONAL = {"国一", "国二"}
PROVINCIAL = {"省一", "省二", "省三"}


def category_for(tier):
    if tier in NATIONAL:
        return "国奖"
    if tier in PROVINCIAL:
        return "省奖"
    return "不获奖"


def predict(total):
    if isinstance(total, bool) or not isinstance(total, (int, float, Decimal)):
        raise ValueError("total must be a number from 0 to 100")
    try:
        value = Decimal(str(total))
    except InvalidOperation as exc:
        raise ValueError("total is not a valid number") from exc
    if not value.is_finite() or not Decimal("0") <= value <= Decimal("100"):
        raise ValueError("total must be between 0 and 100")
    for minimum, forecast, interval, interval_tiers in TIERS:
        if value >= minimum:
            category = category_for(forecast)
            return {
                "total": float(value),
                "category": category,
                "subtier": None if category == "不获奖" else forecast,
                "forecast": forecast,
                "interval": interval,
                "interval_tiers": list(interval_tiers),
                "award_sentence": (
                    f"获奖判断：目前大概率处于{category}范围；"
                    + (
                        f"细分预计为{forecast}（非官方预测）。"
                        if category != "不获奖"
                        else "细分预计为不适用（非官方预测）。"
                    )
                ),
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
