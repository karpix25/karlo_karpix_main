from __future__ import annotations

from pathlib import Path

from services.rule_engine import SpamRuleEngine


def test_rule_engine_rejects_spam(tmp_path: Path) -> None:
    rules = tmp_path / 'sorting_rules.md'
    rules.write_text('- ban: scam\n- prefer: architecture\n', encoding='utf-8')

    engine = SpamRuleEngine(rules)
    result = engine.evaluate('This is scam giveaway text', {'ban_giveaways': True, 'strict_links': True})

    assert result.accepted is False
    assert 'banned_keyword' in result.reason


def test_rule_engine_accepts_technical_post(tmp_path: Path) -> None:
    rules = tmp_path / 'sorting_rules.md'
    rules.write_text('- prefer: architecture\n', encoding='utf-8')

    engine = SpamRuleEngine(rules)
    result = engine.evaluate('Architecture decisions for API and backend scalability', {'prefer_technical_content': True})

    assert result.accepted is True
    assert result.relevance_score >= 0.55
