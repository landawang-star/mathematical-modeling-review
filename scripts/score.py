#!/usr/bin/env python3
"""Compute the project's non-official diagnostic total from five 0–20 scores."""

import json
import sys
import importlib.util
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path


WEIGHTS = {
    "assumptions": Decimal(20),
    "originality": Decimal(25),
    "correctness": Decimal(30),
    "clarity": Decimal(15),
    "compliance": Decimal(10),
}

_AWARD_SPEC = importlib.util.spec_from_file_location("award", Path(__file__).with_name("award.py"))
award = importlib.util.module_from_spec(_AWARD_SPEC)
_AWARD_SPEC.loader.exec_module(award)


def calculate(payload):
    if not isinstance(payload, dict) or set(payload) != set(WEIGHTS):
        raise ValueError(f"input must contain exactly: {', '.join(WEIGHTS)}")

    scores = {}
    missing = []
    for key in WEIGHTS:
        value = payload[key]
        if value is None:
            scores[key] = None
            missing.append(key)
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{key} must be a number from 0 to 20 or null")
        try:
            score = Decimal(str(value))
        except InvalidOperation as exc:
            raise ValueError(f"{key} is not a valid number") from exc
        if not score.is_finite() or not Decimal(0) <= score <= Decimal(20):
            raise ValueError(f"{key} must be between 0 and 20")
        scores[key] = score

    if missing:
        return {
            "total": None,
            "forecast": None,
            "interval": None,
            "unscored": missing,
            "note": "非官方诊断分；缺项不计算总分或奖项预测",
        }

    total = sum((scores[key] / Decimal(20) * weight for key, weight in WEIGHTS.items()), Decimal(0))
    rounded_total = total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    forecast = award.predict(rounded_total)
    return {
        "total": float(rounded_total),
        "forecast": forecast["forecast"],
        "interval": forecast["interval"],
        "unscored": [],
        "note": "非官方诊断分与经验奖项预测；仅适用于五维均已评分的完整 CUMCM 评审",
    }


def main(argv):
    if len(argv) != 2:
        print("usage: python3 scripts/score.py INPUT.json", file=sys.stderr)
        return 2
    try:
        payload = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
        result = calculate(payload)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"score error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
