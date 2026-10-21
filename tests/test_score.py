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

    def test_missing_evidence_prevents_total(self):
        result = score.calculate({
            "assumptions": 18,
            "originality": None,
            "correctness": 17,
            "clarity": 15,
            "compliance": 14,
        })
        self.assertIsNone(result["total"])
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
            (75, "省一"),
            (74.99, "省二"),
            (70, "省二"),
            (69.99, "省三"),
            (60, "省三"),
            (59.99, "暂不预估省级奖"),
        ]
        for total, expected in cases:
            with self.subTest(total=total):
                self.assertEqual(award.predict(total)["forecast"], expected)


if __name__ == "__main__":
    unittest.main()
