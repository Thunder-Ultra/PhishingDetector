# PhishingDetector

A minimal machine-learning phishing detector implemented with pure Python.

## Usage

```python
from phishing_detector import PhishingDetector

detector = PhishingDetector()
detector.train(
    phishing_samples=[
        "verify your account now",
        "urgent update your password",
    ],
    legitimate_samples=[
        "meeting notes for today",
        "project status update",
    ],
)

result = detector.predict("urgent verify your password")
print(result.label, result.score)
```
