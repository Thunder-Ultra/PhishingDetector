from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass


_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class Prediction:
    label: str
    score: float


class PhishingDetector:
    def __init__(self) -> None:
        self._is_trained = False
        self._vocabulary: set[str] = set()
        self._token_counts = {
            "phishing": Counter(),
            "legitimate": Counter(),
        }
        self._doc_counts = {
            "phishing": 0,
            "legitimate": 0,
        }
        self._total_tokens = {
            "phishing": 0,
            "legitimate": 0,
        }

    def train(self, phishing_samples: list[str], legitimate_samples: list[str]) -> None:
        if not phishing_samples or not legitimate_samples:
            raise ValueError("Both phishing_samples and legitimate_samples must be non-empty.")

        self._reset()
        self._fit_class("phishing", phishing_samples)
        self._fit_class("legitimate", legitimate_samples)
        self._is_trained = True

    def predict(self, text: str) -> Prediction:
        if not self._is_trained:
            raise RuntimeError("Model is not trained. Call train() first.")

        tokens = self._tokenize(text)
        phishing_log_prob = self._log_posterior("phishing", tokens)
        legitimate_log_prob = self._log_posterior("legitimate", tokens)
        max_log = max(phishing_log_prob, legitimate_log_prob)
        norm = max_log + math.log(
            math.exp(phishing_log_prob - max_log) + math.exp(legitimate_log_prob - max_log)
        )
        phishing_prob = math.exp(phishing_log_prob - norm)
        label = "phishing" if phishing_prob >= 0.5 else "legitimate"
        score = phishing_prob if label == "phishing" else 1.0 - phishing_prob
        return Prediction(label=label, score=score)

    def _reset(self) -> None:
        self._vocabulary.clear()
        for cls in self._token_counts:
            self._token_counts[cls].clear()
            self._doc_counts[cls] = 0
            self._total_tokens[cls] = 0

    def _fit_class(self, class_name: str, samples: list[str]) -> None:
        self._doc_counts[class_name] = len(samples)
        for sample in samples:
            tokens = self._tokenize(sample)
            self._token_counts[class_name].update(tokens)
            self._total_tokens[class_name] += len(tokens)
            self._vocabulary.update(tokens)

    def _log_posterior(self, class_name: str, tokens: list[str]) -> float:
        total_docs = self._doc_counts["phishing"] + self._doc_counts["legitimate"]
        log_prior = math.log(self._doc_counts[class_name] / total_docs)
        vocab_size = max(len(self._vocabulary), 1)
        class_total_tokens = self._total_tokens[class_name]
        denominator = class_total_tokens + vocab_size
        log_likelihood = 0.0
        token_counter = self._token_counts[class_name]

        for token in tokens:
            token_count = token_counter[token] + 1
            log_likelihood += math.log(token_count / denominator)

        return log_prior + log_likelihood

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return _TOKEN_PATTERN.findall(text.lower())
