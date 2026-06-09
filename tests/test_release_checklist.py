from pathlib import Path


def test_release_checklist_mentions_no_remote_no_push():
    text = Path("docs/release_checklist.md").read_text(encoding="utf-8")
    assert "Git remote is none" in text
    assert "No push performed" in text
    assert "DeepSeek disabled by default" in text
