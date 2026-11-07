#!/usr/bin/env python3
"""Evaluate the required two-stage award forecast and enforce release gates."""

import argparse
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AWARD_SPEC = importlib.util.spec_from_file_location("award", ROOT / "scripts" / "award.py")
award = importlib.util.module_from_spec(AWARD_SPEC)
AWARD_SPEC.loader.exec_module(award)

REQUIRED_CATEGORIES = {"不获奖", "省奖", "国奖"}
AWARDED_CATEGORIES = {"省奖", "国奖"}


def evaluate(rows):
    if not isinstance(rows, list) or not rows:
        raise ValueError("benchmark must be a non-empty list")
    details = []
    for row in rows:
        predicted = award.predict(row["score"])
        actual_category = award.category_for(row["label"])
        details.append({
            "id": row["id"],
            "label": row["label"],
            "evidence": row["evidence"],
            "forecast": predicted["forecast"],
            "actual_category": actual_category,
            "predicted_category": predicted["category"],
            "interval": predicted["interval"],
            "exact": predicted["forecast"] == row["label"],
            "interval_hit": row["label"] in predicted["interval_tiers"],
            "category_hit": predicted["category"] == actual_category,
            "subtier_hit": (
                predicted["subtier"] == row["label"]
                if actual_category in AWARDED_CATEGORIES
                else None
            ),
        })
    count = len(details)
    category_accuracy = sum(item["category_hit"] for item in details) / count
    awarded = [item for item in details if item["actual_category"] in AWARDED_CATEGORIES]
    correctly_routed = [item for item in awarded if item["category_hit"]]
    subtier_accuracy = (
        sum(item["subtier_hit"] for item in correctly_routed) / len(correctly_routed)
        if correctly_routed else None
    )
    end_to_end_subtier_accuracy = (
        sum(item["subtier_hit"] and item["category_hit"] for item in awarded) / len(awarded)
        if awarded else None
    )
    evidence_counts = {}
    for item in details:
        evidence_counts[item["evidence"]] = evidence_counts.get(item["evidence"], 0) + 1
    category_counts = {
        category: sum(item["actual_category"] == category for item in details)
        for category in REQUIRED_CATEGORIES
    }
    return {
        "sample_count": count,
        "evidence_counts": evidence_counts,
        "category_counts": category_counts,
        "first_stage_accuracy": category_accuracy,
        "awarded_sample_count": len(awarded),
        "correctly_routed_awarded_count": len(correctly_routed),
        "subtier_accuracy": subtier_accuracy,
        "end_to_end_subtier_accuracy": end_to_end_subtier_accuracy,
        "details": details,
        "limitations": (
            "回顾性开发集；多数标签为作者自述，不能替代独立盲测。"
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "benchmark", nargs="?", type=Path, default=ROOT / "validation" / "benchmark_v2.10.json"
    )
    parser.add_argument("--gate", action="store_true")
    parser.add_argument("--category-minimum", type=float, default=0.80)
    parser.add_argument("--subtier-minimum", type=float, default=0.70)
    args = parser.parse_args()
    result = evaluate(json.loads(args.benchmark.read_text(encoding="utf-8")))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.gate:
        passed = (
            result["sample_count"] >= 15
            and result["first_stage_accuracy"] >= args.category_minimum
            and result["subtier_accuracy"] is not None
            and result["subtier_accuracy"] >= args.subtier_minimum
        )
        if not passed:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
