"""
Telif/Kopya Kontrolü
DM metni ile AI metni arasında benzerlik kontrolü
"""
import difflib
import logging
import re
from typing import Dict

import config

logger = logging.getLogger(__name__)


class SimilarityChecker:
    def __init__(self, threshold: float = None):
        self.threshold = threshold if threshold is not None else config.SIMILARITY_THRESHOLD

    def normalize(self, text: str) -> str:
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[^a-z0-9äöüß ,.\-_/]", "", text)
        return text.strip()

    def similarity(self, a: str, b: str) -> float:
        a_n = self.normalize(a)
        b_n = self.normalize(b)
        if not a_n or not b_n:
            return 0.0
        return difflib.SequenceMatcher(None, a_n, b_n).ratio()

    def check_fields(self, dm_text: str, ai_text: str) -> Dict:
        sim = self.similarity(dm_text, ai_text)
        status = "OK" if sim <= self.t
