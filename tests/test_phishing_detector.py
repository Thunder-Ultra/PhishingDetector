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
        self.assertLessEqual(prediction.score, 1.0)

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
        self.assertLessEqual(prediction.score, 1.0)

    def test_predict_requires_training(self) -> None:
        detector = PhishingDetector()
        with self.assertRaisesRegex(RuntimeError, "Model is not trained"):
            detector.predict("verify your account")

    def test_train_requires_both_classes(self) -> None:
        detector = PhishingDetector()
        with self.assertRaisesRegex(ValueError, "must be non-empty"):
            detector.train(phishing_samples=[], legitimate_samples=["normal email"])

    def test_train_requires_legitimate_samples(self) -> None:
        detector = PhishingDetector()
        with self.assertRaisesRegex(ValueError, "must be non-empty"):
            detector.train(phishing_samples=["phishing email"], legitimate_samples=[])

    def test_train_requires_tokenizable_samples(self) -> None:
        detector = PhishingDetector()
        with self.assertRaisesRegex(ValueError, "alphanumeric token"):
            detector.train(phishing_samples=["!!!"], legitimate_samples=["..."])


if __name__ == "__main__":
    unittest.main()
