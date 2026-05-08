import unittest

from phishing_detector import PhishingDetector


class PhishingDetectorTests(unittest.TestCase):
    def test_predict_phishing_text(self) -> None:
        detector = PhishingDetector()
        detector.train(
            phishing_samples=[
                "urgent verify account now",
                "suspended account click link",
            ],
            legitimate_samples=[
                "team meeting schedule",
                "project roadmap update",
            ],
        )

        prediction = detector.predict("urgent account verification link")
        self.assertEqual(prediction.label, "phishing")
        self.assertGreaterEqual(prediction.score, 0.5)

    def test_predict_legitimate_text(self) -> None:
        detector = PhishingDetector()
        detector.train(
            phishing_samples=[
                "reset your password immediately",
                "verify billing information now",
            ],
            legitimate_samples=[
                "lunch plans for tomorrow",
                "design review document",
            ],
        )

        prediction = detector.predict("design review tomorrow")
        self.assertEqual(prediction.label, "legitimate")
        self.assertGreaterEqual(prediction.score, 0.5)

    def test_predict_requires_training(self) -> None:
        detector = PhishingDetector()
        with self.assertRaises(RuntimeError):
            detector.predict("verify your account")

    def test_train_requires_both_classes(self) -> None:
        detector = PhishingDetector()
        with self.assertRaises(ValueError):
            detector.train(phishing_samples=[], legitimate_samples=["normal email"])


if __name__ == "__main__":
    unittest.main()
