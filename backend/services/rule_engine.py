from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RuleEvaluation:
    relevance_score: float
    accepted: bool
    reason: str


class SpamRuleEngine:
    def __init__(self, rules_path: Path) -> None:
        self.rules_path = rules_path
        self.ban_keywords: list[str] = []
        self.prefer_keywords: list[str] = []
        self._load_rules()

    def _load_rules(self) -> None:
        if not self.rules_path.exists():
            return

        for raw_line in self.rules_path.read_text(encoding='utf-8').splitlines():
            line = raw_line.strip().lower()
            if line.startswith('- ban:'):
                value = line.split(':', 1)[1].strip()
                if value:
                    self.ban_keywords.append(value)
            if line.startswith('- prefer:'):
                value = line.split(':', 1)[1].strip()
                if value:
                    self.prefer_keywords.append(value)

    def evaluate(self, text: str, skills: dict[str, bool]) -> RuleEvaluation:
        cleaned = text.strip().lower()
        if not cleaned:
            return RuleEvaluation(0.0, False, 'empty_message')

        score = 0.5

        links_count = len(re.findall(r'https?://', cleaned))
        if skills.get('strict_links', True) and links_count > 2:
            return RuleEvaluation(0.05, False, 'too_many_links')

        spam_tokens = ['airdrop', 'giveaway', 'casino', 'bet', 'promo code']
        if skills.get('ban_giveaways', True):
            for token in spam_tokens + self.ban_keywords:
                if token and token in cleaned:
                    return RuleEvaluation(0.1, False, f'banned_keyword:{token}')

        if skills.get('prefer_technical_content', True):
            technical_tokens = ['architecture', 'api', 'backend', 'saas', 'product', 'ai', 'llm']
            if any(token in cleaned for token in technical_tokens):
                score += 0.3

        if self.prefer_keywords and any(token in cleaned for token in self.prefer_keywords):
            score += 0.2

        score = min(score, 1.0)
        accepted = score >= 0.55
        reason = 'accepted' if accepted else 'low_relevance'
        return RuleEvaluation(score, accepted, reason)
