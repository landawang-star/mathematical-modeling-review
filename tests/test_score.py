import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "score.py"
SPEC = importlib.util.spec_from_file_location("score", SCRIPT)
score = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(score)


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


if __name__ == "__main__":
    unittest.main()
