#!/usr/bin/env python3
"""Map a 0–100 diagnostic score to the Skill's two-stage forecast."""

import json
import sys
from decimal import Decimal, InvalidOperation


NATIONAL_TIERS = (
    (Decimal("84"), "国一", "国二至国一", ("国二", "国一")),
    (Decimal("78"), "国二", "省一至国一", ("省一", "国二", "国一")),
)

PROVINCIAL_TIERS = (
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


def predict(total, originality=None):
    if isinstance(total, bool) or not isinstance(total, (int, float, Decimal)):
        raise ValueError("total must be a number from 0 to 100")
    try:
        value = Decimal(str(total))
    except InvalidOperation as exc:
        raise ValueError("total is not a valid number") from exc
    if not value.is_finite() or not Decimal("0") <= value <= Decimal("100"):
        raise ValueError("total must be between 0 and 100")
    originality_value = None
    if originality is not None:
        if isinstance(originality, bool) or not isinstance(originality, (int, float, Decimal)):
            raise ValueError("originality must be a number from 0 to 20")
        originality_value = Decimal(str(originality))
        if not originality_value.is_finite() or not Decimal("0") <= originality_value <= Decimal("20"):
            raise ValueError("originality must be between 0 and 20")

    # National awards require both a high overall score and visible, task-specific
    # contribution. Very high totals retain a national route so one dimension does
    # not become an absolute veto. When originality is unavailable, preserve the
    # legacy score-only behavior but mark the evidence limitation below.
    national_eligible = (
        originality_value is None
        or originality_value >= Decimal("17")
        or value >= Decimal("86")
    )
    tiers = NATIONAL_TIERS + PROVINCIAL_TIERS if national_eligible else PROVINCIAL_TIERS
    for minimum, forecast, interval, interval_tiers in tiers:
        if value >= minimum:
            category = category_for(forecast)
            national_boundary_gap = abs(value - Decimal("84")) if category == "国奖" else None
            return {
                "total": float(value),
                "category": category,
                "subtier": None if category == "不获奖" else forecast,
                "forecast": forecast,
                "interval": interval,
                "interval_tiers": list(interval_tiers),
                "national_tier_boundary": bool(
                    national_boundary_gap is not None and national_boundary_gap <= 2
                ),
                "subtier_confidence_hint": (
                    "低：距国一/国二分界不超过 2 分；还须核查创新证据"
                    if national_boundary_gap is not None and national_boundary_gap <= 2
                    else "待人工核定：分数不能单独证明创新或区分国一、国二"
                    if category == "国奖" else "待人工核定：结合逐问证据与赛区差异"
                ),
                "national_innovation_caveat": (
                    "须核查针对赛题的实质贡献、与常规方案的对照及关键结果的独立验证；"
                    "证据不足时细分置信度为低，并保留国一与国二两种可能。"
                    if category == "国奖" else None
                ),
                "originality_gate": {
                    "available": originality_value is not None,
                    "score": float(originality_value) if originality_value is not None else None,
                    "national_eligible": national_eligible,
                    "rule": "创造性≥17，或总分≥86；缺创造性分时退回总分映射并降低置信度",
                },
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
    if len(argv) not in (2, 3):
        print("usage: python3 scripts/award.py TOTAL [ORIGINALITY]", file=sys.stderr)
        return 2
    try:
        originality = Decimal(argv[2]) if len(argv) == 3 else None
        result = predict(Decimal(argv[1]), originality)
    except (InvalidOperation, ValueError) as exc:
        print(f"award error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
