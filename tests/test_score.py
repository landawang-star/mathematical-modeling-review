import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "score.py"
SPEC = importlib.util.spec_from_file_location("score", SCRIPT)
score = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(score)

AWARD_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "award.py"
AWARD_SPEC = importlib.util.spec_from_file_location("award", AWARD_SCRIPT)
award = importlib.util.module_from_spec(AWARD_SPEC)
AWARD_SPEC.loader.exec_module(award)


class ScoreTests(unittest.TestCase):
    def test_weighted_total_is_not_raw_sum(self):
        result = score.calculate({
            "assumptions": 18,
            "originality": 16,
            "correctness": 17,
            "clarity": 15,
            "compliance": 14,
        })
        self.assertEqual(result["total"], 81.75)
        self.assertEqual(result["forecast"], "国二")
        self.assertEqual(result["category"], "国奖")
        self.assertEqual(result["subtier"], "国二")
        self.assertEqual(result["interval"], "省一至国一")
        self.assertEqual(result["interval_tiers"], ["省一", "国二", "国一"])

    def test_missing_evidence_prevents_total(self):
        result = score.calculate({
            "assumptions": 18,
            "originality": None,
            "correctness": 17,
            "clarity": 15,
            "compliance": 14,
        })
        self.assertIsNone(result["total"])
        self.assertIsNone(result["forecast"])
        self.assertEqual(result["unscored"], ["originality"])

    def test_out_of_range_is_rejected(self):
        with self.assertRaises(ValueError):
            score.calculate({key: 21 for key in score.WEIGHTS})

    def test_missing_or_extra_key_is_rejected(self):
        with self.assertRaises(ValueError):
            score.calculate({"assumptions": 18})

    def test_award_forecast_thresholds(self):
        cases = [
            (84, "国一"),
            (83.99, "国二"),
            (78, "国二"),
            (77.99, "省一"),
            (70, "省一"),
            (69.99, "省二"),
            (65, "省二"),
            (64.99, "省三"),
            (60, "省三"),
            (59.99, "不获奖"),
        ]
        for total, expected in cases:
            with self.subTest(total=total):
                self.assertEqual(award.predict(total)["forecast"], expected)

    def test_two_stage_categories(self):
        cases = [
            (84, "国奖", "国一"),
            (78, "国奖", "国二"),
            (70, "省奖", "省一"),
            (65, "省奖", "省二"),
            (60, "省奖", "省三"),
            (59.99, "不获奖", None),
        ]
        for total, category, subtier in cases:
            with self.subTest(total=total):
                result = award.predict(total)
                self.assertEqual(result["category"], category)
                self.assertEqual(result["subtier"], subtier)

    def test_award_sentence_is_direct_and_non_official(self):
        result = award.predict(73)
        self.assertEqual(
            result["award_sentence"],
            "获奖判断：目前大概率处于省奖范围；细分预计为省一（非官方预测）。",
        )

    def test_intervals_cover_adjacent_downside_and_upside(self):
        cases = [
            (84, ["国二", "国一"]),
            (78, ["省一", "国二", "国一"]),
            (70, ["省二", "省一", "国二"]),
            (65, ["省三", "省二", "省一"]),
            (60, ["不获奖", "省三", "省二"]),
        ]
        for total, expected in cases:
            with self.subTest(total=total):
                self.assertEqual(award.predict(total)["interval_tiers"], expected)


if __name__ == "__main__":
    unittest.main()
