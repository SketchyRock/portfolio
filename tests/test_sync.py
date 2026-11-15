import json

import pytest

import sync

INCLUDE = ["**/*retrospective*.md", "**/*overview*.md"]


def test_allowlist():
    ok = ["ICPC-2025/ICPC-retrospective.md",
          "VMI-CyberFusion-2026/Compressed-ctf-solver-overview.md",
          "top-Retrospective.MD", "A/B/c-OVERVIEW.md"]
    bad = ["MACCDC-2026/Qualifier/MACCDC-Palo-Alto-reference.md",
           "MACCDC-2026/Qualifier/2026MACCDCQTeamPackv1-1.pdf",
           "README.md", "x/retrospective.pdf", "x/notes.txt"]
    assert all(sync.is_allowed(p, INCLUDE) for p in ok)
    assert not any(sync.is_allowed(p, INCLUDE) for p in bad)


def test_empty_and_draft_skipped():
    tree = [{"type": "blob", "path": f"e/{n}-retrospective.md"} for n in ("a", "b", "c", "d", "ok")]
    texts = {"e/a-retrospective.md": "   \n",
             "e/b-retrospective.md": "---\ndraft: true\n---\n# B\n",
             "e/c-retrospective.md": "# C\n<!-- draft -->\n",
             "e/d-retrospective.md": "",
             "e/ok-retrospective.md": "# Ok\n"}
    out = sync.build_writeups(tree, texts.__getitem__, INCLUDE)
    assert [p["slug"] for p in out] == ["ok-retrospective"]


def test_blocked_file_never_fetched():
    tree = [{"type": "blob", "path": "MACCDC-2026/Qualifier/MACCDC-Palo-Alto-reference.md"}]
    def boom(path):
        raise AssertionError("fetched a non-allowlisted file")
    assert sync.build_writeups(tree, boom, INCLUDE) == []


def test_slug_and_collision():
    assert sync.slug_for("ICPC-2025/ICPC-retrospective.md") == "icpc-retrospective"
    s = sync.assign_slugs(["A/x-retrospective.md", "B/x-retrospective.md", "C/y-overview.md"])
    assert s["A/x-retrospective.md"] == "a-x-retrospective"
    assert s["B/x-retrospective.md"] == "b-x-retrospective"
    assert s["C/y-overview.md"] == "y-overview"


def test_title():
    assert sync.get_title("intro\n# Real Title\n", "a/b.md") == "Real Title"
    assert sync.get_title("no heading", "a/my-first-post.md") == "My First Post"


def test_date_parsing():
    assert sync.parse_date("# T\n**Date:** 1/17/2026\n") == ("1/17/2026", "Jan 2026", "2026-01-17")
    assert sync.parse_date("# T\n") == ("", "", "")


def test_writeup_without_date():
    w = sync.build_writeup("E/y-overview.md", "y-overview", "# Y\n")
    assert (w["date"], w["sort_key"], w["event"], w["type"]) == ("", "", "E", "")
    assert w["source_url"].endswith("/blob/HEAD/E/y-overview.md")


def test_failure_keeps_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(sync, "CACHE", str(tmp_path))
    (tmp_path / "repos.json").write_text("[1]")
    (tmp_path / "writeups.json").write_text("[2]")
    def fail(*a, **k):
        raise sync.SyncError("down")
    monkeypatch.setattr(sync, "fetch_json", fail)
    assert sync.run() is False
    assert json.loads((tmp_path / "repos.json").read_text()) == [1]


def test_failure_without_cache_exits(tmp_path, monkeypatch):
    monkeypatch.setattr(sync, "CACHE", str(tmp_path))
    def fail(*a, **k):
        raise sync.SyncError("down")
    monkeypatch.setattr(sync, "fetch_json", fail)
    with pytest.raises(SystemExit):
        sync.run()


def test_clean_repos_drops_forks_private_and_hidden():
    raw = [{"name": "a", "html_url": "u", "fork": True},
           {"name": "secret", "html_url": "u", "private": True},
           {"name": "SketchyRock", "html_url": "u"},
           {"name": "keep", "html_url": "u", "language": "Go"}]
    out = sync.clean_repos(raw, ["sketchyrock"])
    assert [r["name"] for r in out] == ["keep"]


def test_front_matter_drives_title_date_and_type():
    text = '---\ntitle: "Demo Event"\ntype: "retrospective"\ndate: 2026-02\n---\n\n# Demo Event\n\nBody.\n'
    meta, body = sync.split_front_matter(text)
    assert meta["type"] == "retrospective" and body.lstrip().startswith("# Demo Event")
    post = sync.build_writeup("2026/demo.md", "demo", text)
    assert (post["title"], post["date"], post["sort_key"]) == ("Demo Event", "Feb 2026", "2026-02-01")
    assert post["type"] == "retrospective"
    assert "type:" not in post["markdown"]


def test_types_filter_skips_other_documents():
    tree = [{"type": "blob", "path": "2026/a.md"}, {"type": "blob", "path": "2026/b.md"}]
    texts = {"2026/a.md": "---\ntype: retrospective\n---\n# A\n", "2026/b.md": "---\ntype: reference\n---\n# B\n"}
    out = sync.build_writeups(tree, texts.__getitem__, ["20??/*.md"], types=["retrospective"])
    assert [p["slug"] for p in out] == ["a"]
